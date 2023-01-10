from aiogram import F, Bot, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from Bot.keyboards.main_keys import back_button
from Bot.keyboards.transaction_keys import trans_token_kb, trans_network_kb, kb_confirm_transfer, m_transaction
from Bot.keyboards.wallet_keys import addresses_kb
from Bot.states.trans_states import Trs_transfer, TransactionStates
from Bot.states.wallet_states import WalletStates
from Bot.utilts.ContentService import ContentService
from Bot.utilts.FunctionalService import perform_sending
from Bot.utilts.fee_strategy import getFeeStrategy
from Bot.utilts.mmanager import MManager
from _config.settings import DEBUG_MODE
from Dao.DB_Redis import DataRedis
from Dao.models.Address import Address
from Dao.models.Owner import Owner
from Dao.models.Token import Token
from Dao.models.Transaction import Transaction
from Dao.models.bot_models import ContentUnit
from Services.EntServices.AddressService import AddressService
from Services.EntServices.OwnerService import OwnerService
from Services.EntServices.TokenService import TokenService

router = Router()


@router.callback_query(F.data == "back", StateFilter(Trs_transfer.set_network))
@router.callback_query(F.data == "send", StateFilter(WalletStates))
async def start_transfer(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await state.set_state(Trs_transfer.new_transfer)
    content: ContentUnit = await ContentUnit(tag="transfer_choose_currency").get()
    all_tokens_list = await TokenService.all_tokens()
    await MManager.content_surf(event=callback, state=state, bot=bot, content_unit=content,
                                keyboard=trans_token_kb(all_tokens_list),
                                placeholder_text="Выберите валюту для отправки:")


@router.callback_query(F.data == "back", StateFilter(Trs_transfer.address))
@router.callback_query(F.data.startswith("tToken_"), StateFilter(Trs_transfer.new_transfer))
async def choose_network(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    if callback.data != 'back':
        token_name = callback.data.split('_')[-1]
    else:
        token_name = data.get('token_name')
    await state.update_data(token_name=token_name)
    await state.set_state(Trs_transfer.set_network)
    text = "<b>Выберите сеть:</b>"
    content: ContentUnit = await ContentUnit(tag="transfer_choose_network").get()
    algos = await TokenService.alorithms_for_token_name(token_name=token_name)
    await MManager.content_surf(event=callback, state=state, bot=bot, content_unit=content,
                                keyboard=trans_network_kb(algos),
                                placeholder_text=text)


@router.callback_query(F.data == "back", StateFilter(Trs_transfer.confirm_transfer, Trs_transfer.amount))
@router.callback_query(F.data.startswith("tAlgos_"), StateFilter(Trs_transfer.set_network))
async def algorithm_use(callback: CallbackQuery, bot: Bot, state: FSMContext):
    data = await state.get_data()
    if callback.data != "back":
        algo = callback.data.split('_')[-1]
    else:
        algo = data.get("algorithm")
    token_name = data.get("token_name")

    main_net = not DEBUG_MODE
    token_obj: Token = await TokenService.get_token(token_name=token_name, token_algorithm=algo, main_net=main_net)

    if token_obj.algorithm.blockchain == token_obj.network.blockchain:
        blockchain = token_obj.algorithm.blockchain
    else:
        raise Exception("Bases are broken!")

    # TODO ПРОВЕРКА АДРЕСА

    u_id = await DataRedis.find_user(int(callback.from_user.id))
    chain_address = await OwnerService().get_chain_address(u_id, blockchain)

    fee = await getFeeStrategy(token_obj)
    frozen_fee = chain_address.get_address_freezed_fee(token_name)
    balance_info = await AddressService().get_address_balances(chain_address.address, [token_obj])
    token_balance = balance_info.get(token_name, 0.0)

    await state.update_data(contract_Id=token_obj.contract_Id)
    await state.update_data(u_address=chain_address.address)
    await state.update_data(algorithm=algo)
    await state.update_data(balance=token_balance)
    await state.update_data(frozen_fee=frozen_fee)
    await state.update_data(fee=fee)
    await state.update_data(blockchain=blockchain)

    placeholder_text = "Выбранная валюта: {token_name}\n" \
                       "Выбранная сеть: {network}\n" \
                       "Минимальная сумма отправки: 3 USDT\n" \
                       "Комиссия: {fee} USDT"
    content: ContentUnit = await ContentUnit(tag="trans_token_conditions").get()
    content.add_formatting_vars(token_name=token_obj.token_name, network=token_obj.algorithm.name, fee=fee)
    msg = await ContentService.send(content=content, bot=bot,
                                    chat_id=callback.message.chat.id,
                                    placeholder_text=placeholder_text)
    await MManager.garbage_store(state, msg.message_id)

    addresses = await OwnerService.get_all_chain_addresses(u_id=u_id, blockchain=blockchain)
    content: ContentUnit = await ContentUnit(tag="trans_addresses_for_trans").get()
    counter = 1
    adresses_dict = dict()
    addresses_text = str()
    for address in addresses:
        address_name = address.name if address.name else ""
        addresses_text += f"{counter}. " + address_name + f" <code>{address.address}</code>\n"
        if address.name:
            adresses_dict.update({address.name: address.address})
        else:
            adresses_dict.update({counter: address.address})
        counter += 1
    await state.update_data(from_addresses=adresses_dict)

    placeholder_text = "Доступные адреса:\n\n" \
                       "{addresses_list}\n\n" \
                       "Выберите адрес c которого хотите отправить"
    content.add_formatting_vars(addresses_list=addresses_text)

    await MManager.content_surf(event=callback.message, state=state, bot=bot, content_unit=content,
                                placeholder_text=placeholder_text, keyboard=addresses_kb(adresses_dict, new_button=False))
    await state.set_state(Trs_transfer.address)


@router.callback_query(StateFilter(Trs_transfer.address))
async def choosen_address(callback: CallbackQuery, bot: Bot, state: FSMContext, session: AsyncSession):
    address_nmbr = callback.data
    data = await state.get_data()
    from_addresses = data.get('from_addresses')
    algo = data.get("algorithm")
    token_name = data.get('token_name')

    address: Address = await session.get(Address, from_addresses.get(address_nmbr))

    main_net = not DEBUG_MODE
    token_obj: Token = await TokenService.get_token(token_name=token_name, token_algorithm=algo, main_net=main_net)
    balance = await AddressService.get_address_balances(address=address.address, specific=[token_obj])
    await state.update_data(address=address.address)
    await state.update_data(balance=balance[token_name])

    content: ContentUnit = await ContentUnit(tag="trans_choose_amount").get()
    placeholder_text = "Выбранный адрес:\n\n<code>{address}</code>\n\nВыберите сумму которую хотите отправить:"
    content.add_formatting_vars(address=address.address)
    await MManager.content_surf(event=callback, state=state, bot=bot, content_unit=content,
                                placeholder_text=placeholder_text)
    await state.set_state(Trs_transfer.amount)


@router.message(StateFilter(Trs_transfer.amount))
async def choose_amount(message: Message, bot: Bot, state: FSMContext):
    if not message.text.replace(".", "", 1).isdigit():
        await message.answer("Вы указали неверное значение, пожалуйста укажите сумму для перевода в виде числа")
        return
    else:
        amount = float(message.text)

    s_data = await state.get_data()
    token_name = s_data.get("token_name")
    balance = s_data.get("balance")
    frozen_fee = s_data.get("frozen_fee")
    fee = s_data.get("fee")
    algo = s_data.get('algorithm')

    if balance - frozen_fee < amount + fee:
        missing = float(amount + fee) - float(balance)
        content: ContentUnit = await ContentUnit(tag="trans_not_enough").get()
        text = "Для перевода вам не хватает: {missing} {token}\n\n" \
               "Пожалуйста укажите другую сумму или пополните баланс\n\n" \
               "Ваш баланс: {balance} {token}\n" \
               "Комиссия: {fee} {token}"
        content.add_formatting_vars(missing=missing, token=token_name, balance=balance - frozen_fee, fee=fee)
        keyboard = back_button()
    else:
        await state.set_state(Trs_transfer.choose_where)
        text = "Введите адрес на который хотите отправить {token} в сети {network} или UID пользователя"
        await state.update_data(amount=amount)
        content: ContentUnit = await ContentUnit(tag="trans_choose_where").get()
        content.add_formatting_vars(token=token_name, network=algo)
        keyboard = None

    await MManager.content_surf(event=message, state=state, bot=bot, content_unit=content, placeholder_text=text,
                                keyboard=keyboard)


@router.message(StateFilter(Trs_transfer.choose_where))
async def transfer_info(message: Message, bot: Bot, state: FSMContext):
    to_address = message.text
    s_data = await state.get_data()
    token_name = s_data.get("token_name")
    algorithm_name = s_data.get("algorithm")
    amount = s_data.get("amount")
    from_address = s_data.get("address")
    fee = s_data.get("fee")
    info_text = "Выбранная валюта: {token}\n" \
                "Выбранная сеть: {network}\n" \
                "Кошелек отправки: {wallet}\n" \
                "Кошелек получения: {second_wallet}\n" \
                "Сумма перевода: {amount} {token}\n" \
                "Комиссия: {fee}\n" \
                "Сумма к получению: {final_sum}\n"
    content: ContentUnit = await ContentUnit(tag="trans_final_info").get()
    content.add_formatting_vars(token=token_name, network=algorithm_name, wallet=from_address, second_wallet=to_address,
                            amount=amount, fee=fee, final_sum=amount - fee)

    await state.update_data(algorithm_name=algorithm_name)
    await state.update_data(to_address=to_address)
    await state.set_state(Trs_transfer.confirm_transfer)
    await MManager.content_surf(event=message, state=state, bot=bot, content_unit=content, placeholder_text=info_text,
                                keyboard=kb_confirm_transfer())


@router.callback_query(lambda call: "confirm_transfer_token" in call.data, StateFilter(Trs_transfer.confirm_transfer))
async def confirm(callback: CallbackQuery, bot: Bot, state: FSMContext, session: AsyncSession):
    message = await bot.send_message(chat_id=callback.from_user.id, text="Устанавливается связь с блокчейном...")
    s_data = await state.get_data()
    token_name = s_data.get("token_name")
    contract_Id = s_data.get("contract_Id")
    algorithm_name = s_data.get("algorithm_name")
    to_address = s_data.get("to_address")
    blockchain = s_data.get("blockchain")
    amount = s_data.get("amount")

    u_id = await DataRedis.find_user(int(callback.from_user.id))

    owner: Owner = await session.get(Owner, u_id)
    address: Address = AddressService.get_address_for_transaction(owner, blockchain, contract_Id)

    main_net = not DEBUG_MODE
    token = await TokenService.get_token(token_name=token_name, token_algorithm=algorithm_name, main_net=main_net)
    if not token:
        raise Exception(
            f"TOKEN {token_name} {algorithm_name} {'MAINNET' if main_net else 'TESTNET'} NOT FOUND IN GIVEN ")
    transaction: Transaction = await perform_sending(address, amount, token, to_address, message, callback.from_user.id)
    text = ("ID транзакции: {trans_id}\n"
            "Выбранная валюта: {token}\n"
            "Выбранная сеть: {network}\n"
            "Кошелек отправки: {wallet}\n"
            "Кошелек получения: {second_wallet}\n"
            "\n"
            "Сумма перевода: {amount} {token}\n"
            "Комиссия: {fee}\n"
            "Сумма к получению: {final_sum}\n"
            "\n"
            "Исполнена!")
    await state.set_state(TransactionStates.main)

    content: ContentUnit = await ContentUnit(tag="trans_result").get()
    content.add_formatting_vars(trans_id=transaction.id,
                            token=transaction.token.token_name, network=transaction.token.algorithm_name,
                            wallet=transaction.address.address, second_wallet=transaction.foreign_address,
                            amount=transaction.amount, final_sum=transaction.amount)
    await MManager.content_surf(event=message, state=state, bot=bot, content_unit=content,
                                keyboard=m_transaction(),
                                placeholder_text=text)
