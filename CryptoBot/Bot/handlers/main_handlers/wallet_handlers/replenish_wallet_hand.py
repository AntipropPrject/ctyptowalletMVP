from aiogram import Router, Bot, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, BufferedInputFile
from sqlalchemy.ext.asyncio import AsyncSession

from Bot.keyboards.main_keys import back_button
from Bot.keyboards.wallet_keys import add_token_kb, network_kb, addresses_kb, wallet_view_kb
from Bot.states.wallet_states import WalletStates
from Bot.utilts.ContentService import ContentService
from Bot.utilts.currency_helper import blockchains
from Bot.utilts.mmanager import MManager
from Bot.utilts.qr_code_generator import pretty_qr_code
from Dao.DB_Redis import DataRedis
from Dao.models.Address import Address
from Dao.models.bot_models import ContentUnit
from Services.EntServices.OwnerService import OwnerService
from Services.EntServices.TokenService import TokenService

router = Router()


@router.callback_query(F.data == 'back', StateFilter(WalletStates.replenish_network))
@router.callback_query(F.data == "replenish", StateFilter(WalletStates))
@MManager.garbage_manage(store=False, clean=True)
async def replenish_choose_currency(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await state.set_state(WalletStates.replenish_token)
    content: ContentUnit = await ContentUnit(tag="repl_choose_currency").get()
    all_tokens_list = await TokenService.all_tokens()
    await MManager.content_surf(event=callback, state=state, bot=bot, content_unit=content,
                                keyboard=add_token_kb(all_tokens_list),
                                placeholder_text=f"Выберите валюту:")


@router.callback_query(F.data == 'back', StateFilter(WalletStates.choose_address))
@router.callback_query(F.data.startswith("new_t"), StateFilter(WalletStates.replenish_token))
@MManager.garbage_manage(store=False, clean=True)
async def add_network(callback: CallbackQuery, state: FSMContext, bot: Bot):
    if callback.data == 'back':
        data = await state.get_data()
        token = data.get('token')
    else:
        token = callback.data.replace('new_t_', "")
        await state.update_data(token=token)
    await state.set_state(WalletStates.replenish_network)
    content: ContentUnit = await ContentUnit(tag="repl_choose_network").get()
    algos = await TokenService.alorithms_for_token_name(token_name=token)
    await MManager.content_surf(event=callback, state=state, bot=bot, content_unit=content,
                                keyboard=network_kb(custom_network_list=algos),
                                placeholder_text=f"Выберите сеть:")


@router.callback_query(F.data.startswith("my_adresses"), StateFilter(WalletStates.choose_address))
@router.callback_query(F.data.startswith("new_n"), StateFilter(WalletStates.replenish_network))
async def complete_token(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await state.set_state(WalletStates.choose_address)
    data = await state.get_data()
    token_name = data.get('token')
    if callback.data == 'my_adresses':
        network_name = data.get('network')
    else:
        network_name = callback.data.replace("new_n_", "")
        await state.update_data(network=network_name)

    content: ContentUnit = await ContentUnit(tag="replenish_info").get()
    content.add_formatting_vars(token_name=token_name, network=network_name,
                                 repl_min=2, comission=0, approvals=20)
    placeholder_text = "Выбранная валюта: <code>{token_name}</code>\n" \
                "Выбранная сеть: <code>{network}</code>\n" \
                "Минимальная сумма пополнения: {repl_min}\n" \
                "Комиссия: {comission}\n" \
                "Необходимое количество подтверждений: {approvals}"
    msg = await ContentService.send(content, bot, chat_id=callback.message.chat.id, placeholder_text=placeholder_text)
    await MManager.garbage_store(state, msg.message_id)

    chain = [i for i in blockchains if network_name in blockchains[i]['networks']][0]
    u_id = await DataRedis.find_user(callback.from_user.id)
    addresses = await OwnerService.get_all_chain_addresses(u_id, chain)

    content: ContentUnit = await ContentUnit(tag="replenish_addresses").get()
    info_text = "Доступные адреса:\n\n"

    counter = 1
    adresses_dict = dict()
    for address in addresses:
        info_text += f"{counter}. <code>{address}</code>\n"
        adresses_dict.update({counter: address})
        counter += 1
    await state.update_data(adresses=adresses_dict)
    if content.text:
        content.text = content.text.format(info_text=info_text)
    await MManager.content_surf(event=callback.message, state=state, bot=bot, content_unit=content,
                                keyboard=addresses_kb(counter), placeholder_text=info_text)


@router.callback_query(F.data == 'back', StateFilter(WalletStates.qr))
@router.callback_query(F.data.isdigit(), StateFilter(WalletStates.choose_address))
@MManager.garbage_manage(store=False, clean=True)
async def address_inspect(callback: CallbackQuery, state: FSMContext, bot: Bot, session: AsyncSession):
    await state.set_state(WalletStates.choose_address)
    address_nmbr = callback.data
    data = await state.get_data()
    if callback.data == 'back':
        address_str = data.get('chosen_address')
    else:
        adresses = data.get('adresses')
        address_str = adresses.get(address_nmbr)
    address: Address = await session.get(Address, address_str)
    content: ContentUnit = await ContentUnit(tag="replenish_address_view").get()
    info_text = 'Выбранный адрес: <code>{address}</code>\n\n*Нажмите на адрес, чтобы скопировать.'
    content.add_formatting_vars(address=address.address)
    if content.text:
        content.text = content.text.format(address=address.address)

    await state.update_data(chosen_address=address.address)

    content.media_type = 'photo'
    await MManager.content_surf(event=callback.message, state=state, bot=bot, content_unit=content,
                                placeholder_text=info_text, keyboard=wallet_view_kb())


@router.callback_query(F.data == 'QRFK', StateFilter(WalletStates.choose_address))
@MManager.garbage_manage(store=False, clean=True)
async def qr_ghan(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await state.set_state(WalletStates.qr)
    data = await state.get_data()
    address = data.get('chosen_address')

    qr = await pretty_qr_code(address)
    content: ContentUnit = await ContentUnit(tag="qrcd").get()
    content.media_id = BufferedInputFile(file=qr, filename=str(address) + ".png")
    content.media_type = 'photo'
    content.add_formatting_vars(address=address)
    await MManager.content_surf(event=callback.message, state=state, bot=bot, content_unit=content,
                                placeholder_text='Ваш QR код для пополнения кошелька', keyboard=back_button())
