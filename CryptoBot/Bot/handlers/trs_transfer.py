from aiogram import Router, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import hlink
from sqlalchemy.ext.asyncio import AsyncSession

from Bot.handlers.loading_handler import loader
from Bot.handlers.transaction_hand import transaction_start
from Bot.keyboards.transaction_keys import trans_network_kb, change_transfer_token, \
    kb_confirm_transfer
from Bot.states.trans_states import Trs_transfer, TransactionStates
from Bot.utilts.currency_helper import base_tokens, blockchains
from Bot.utilts.settings import DEBUG_MODE
from Dao.models.Owner import Owner
from Services.owner_service import OwnerService
from crypto.TRON_wallet import Tron_wallet

router = Router()
router.message.filter(StateFilter(Trs_transfer))
tron = Tron_wallet()


@router.callback_query(lambda call: "transferToken_" in call.data, StateFilter(Trs_transfer.new_transfer))
async def start_transfer(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.set_state(Trs_transfer.set_network)
    data = callback.data.split('_')
    token = data[-1]
    await state.update_data(token=token)
    text = "Перевод: token\nБаланс: Не определен\nСеть: Не выбрана\n" \
           "Адрес получателя: Не известен\nСумма: 0\n\n"
    text = text.replace("token", token)
    await state.update_data(text=text)

    network = ["TRC-20"]
    text = text + "В какой сети вы хотите перевести токен?"
    message = await callback.message.answer(text, reply_markup=trans_network_kb(network))
    await state.update_data(message_id=message.message_id)


@router.callback_query(lambda call: "transferNetwork_" in call.data, StateFilter(Trs_transfer.set_network))
async def start_transfer(callback: CallbackQuery, bot: Bot, state: FSMContext):
    sdata = await state.get_data()
    cdata = callback.data.split('_')
    token = sdata.get("token")
    network = cdata[-1]
    token_info = base_tokens.get(token, None)
    owner = OwnerService()

    if token_info is not None:  # TODO Это надо вешать на удобные функции и модели
        if DEBUG_MODE:
            contract_address = token_info.get("testnet_contract_address")
        else:
            contract_address = token_info.get("contract_address")
    else:
        contract_address = None
        # пользовательский контракт
        pass
    await state.update_data(contract_address=contract_address)

    tron_address = await owner.get_chain_address(int(callback.from_user.id), 'tron')
    if token == "TRX":  # TODO Это надо вешать на удобные функции и модели
        balance = await tron.TRX_get_balance(tron_address.address)
    elif network in blockchains.get("tron").get("networks"):
        balance = await tron.TRC_20_get_balance(contract_address, tron_address.address)
    else:
        raise ValueError("Network not supported")

    text = sdata.get("text")
    text = text.replace("Не выбрана", network)
    text = text.replace("Не определен", str(balance))
    message_id = sdata.get("message_id")
    await state.update_data(network=network)
    await state.update_data(balance=balance)
    await state.update_data(text=text)
    text = text + "Напишите адрес получателя"
    await state.set_state(Trs_transfer.address)
    await bot.edit_message_text(text, callback.from_user.id, message_id, reply_markup=change_transfer_token())


@router.message(StateFilter(Trs_transfer.address))
async def address(message: Message, state: FSMContext, bot: Bot):
    sdata = await state.get_data()
    text = sdata.get("text")
    message_id = sdata.get("message_id")
    address = message.text
    token = sdata.get("token")
    text = text.replace("Не известен", address)
    text = text + f"Напишите сумму для перевода в {token}"
    await state.update_data(address=address)
    await state.set_state(Trs_transfer.confirm_transfer)
    await bot.edit_message_text(text, message.from_user.id, message_id, reply_markup=change_transfer_token())


@router.message(StateFilter(Trs_transfer.confirm_transfer))
async def confirm_transfer(message: Message, state: FSMContext):
    await message.delete()
    sdata = await state.get_data()
    fee = 1.0
    amount = float(message.text)
    balance = sdata.get("balance")
    token = sdata.get("token")

    if balance < amount + fee:
        lacks_fee = (amount + fee) - balance
        await message.answer(f"Вашего баланса недостаточно для перевода данной суммы:\n\n"
                             f"Баланс: {balance} {token}\n"
                             f"Комиссия сети: {fee} {token}\n\n"
                             f"Для перевода не хватает: {lacks_fee} {token}")
        await message.answer("Пожалуйста напишите новую сумму или пополните баланс")
    else:
        network = sdata.get("network")
        to_address = sdata.get("address")
        await state.update_data(amount=amount)
        await state.update_data(fee=fee)
        text = f"Внимание! Вы совершаете транзакцию!\n________________________\n" \
               f"Перевод: {token}\nСеть: {network}\nАдрес получателя: {to_address}\n" \
               f"_________________________\nКомиссия: {fee} {token}\nСумма: {amount} {token}"
        await state.set_state(Trs_transfer.transfer)
        await message.answer(text, reply_markup=kb_confirm_transfer())


@router.callback_query(lambda call: "confirm_transfer_token" in call.data, StateFilter(Trs_transfer.transfer))
async def start_transfer(callback: CallbackQuery, bot: Bot, state: FSMContext, session: AsyncSession):
    await callback.message.delete()
    await loader(chat_id=callback.from_user.id, text="Пожалуйста дождитесь завершения, транзакция выполняется",
                 time=20)
    owner: Owner = await session.get(Owner, str(callback.from_user.id))

    sdata = await state.get_data()
    contract_address = sdata.get("contract_address")
    network = sdata.get("network")
    to_address = sdata.get("address")
    amount = sdata.get("amount")
    fee = sdata.get("fee")

    if network in blockchains.get("tron").get("networks"):
        wallet_private_key = list(owner.wallets.get("tron").addresses.values())[0].private_key
        wallet_address = list(owner.wallets.get("tron").addresses.values())[0].address
        if network == "TRC-10":
            pass
        if network == "TRC-20":

            th = await tron.TRC_20_transfer(wallet_private_key, contract_address,
                                            wallet_address, to_address, float(amount))
            if th.get("status") == "SUCCESS":
                await state.set_state(TransactionStates.main)
                link = hlink('ссылке', th.get("txn_id"))
                await callback.message.answer(
                    f"Транзакция завершена!\n\nПроверить статус транзакции вы можете по {link}")
                await transaction_start(callback.message, bot, state)
            else:
                await transaction_start(callback.message, bot, state)
                await callback.answer("Ошибка транзакции")
                await state.set_state(TransactionStates.main)


@router.callback_query(lambda call: "cancel_transfer_token" in call.data, StateFilter(Trs_transfer.transfer))
async def start_transfer(callback: CallbackQuery, bot: Bot, state: FSMContext):
    await state.set_state(TransactionStates.main)
    await callback.message.delete()
    await callback.message.answer("Ваша транзакция отменена")
    await transaction_start(callback.message, bot, state)
