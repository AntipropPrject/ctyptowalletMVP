from aiogram import F, Bot, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from Bot.keyboards.main_keys import back_button
from Bot.keyboards.tran_history_keys import trans_history_kb
from Bot.keyboards.wallet_keys import trans_history_start
from Bot.states.trans_states import Trs_transfer
from Bot.states.wallet_states import WalletStates
from Bot.utilts.mmanager import MManager
from Dao.DB_Redis import DataRedis
from Dao.models.bot_models import ContentUnit
from Services.EntServices.TransactionService import TransactionService

router = Router()


@router.callback_query(F.data == "back", StateFilter(WalletStates.transaction_history_send))
@router.callback_query(F.data == "full_history", StateFilter(WalletStates, Trs_transfer))
async def tran_history_start(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await state.set_state(WalletStates.transaction_history_start)
    await state.update_data(transaction_page=1)

    content: ContentUnit = await ContentUnit(tag="trans_history_start").get()
    placeholder_text = f"Выберите тип транзакций:"
    await MManager.content_surf(event=callback, state=state, bot=bot, content_unit=content,
                                keyboard=trans_history_start(),
                                placeholder_text=placeholder_text)


@router.callback_query(F.data.endswith("_history"), StateFilter(WalletStates))
@router.callback_query(F.data == "next_page_tsend", StateFilter(WalletStates))
async def tran_history_send(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await state.set_state(WalletStates.transaction_history_send)
    u_id = await DataRedis.find_user(callback.from_user.id)
    data = await state.get_data()
    transaction_page = data.get('transaction_page')
    address = None
    if callback.data == "next_page_tsend":
        tr_type = data.get('trans_type')
        transaction_page += 1
        await state.update_data(transaction_page=transaction_page)
    else:
        callback_data_list = callback.data.split('_')
        tr_type = callback_data_list[0]
        if 'address' in callback.data:
            address = data.get('chosen_address')
        if tr_type == 'uid':
            tr_type = None

    trans_list = await TransactionService.get_user_transactions(u_id, transaction_type=tr_type, address=address)

    if 'uid' in callback.data:
        trans_list = [transaction for transaction in trans_list if transaction.foreign_related_UID]

    if trans_list:
        page_list = trans_list[transaction_page*5-1:transaction_page*5+4]
        content: ContentUnit = await ContentUnit(tag="trans_history_send").get()
        max_pages = round(len(trans_list)/5)
        placeholder_text = f"Страница {transaction_page}/{max_pages}\n\n" \
                           f"Статус:\n🔄 - Обработка\n✅ - Успешно\n🅾️ - Отменен"
        if transaction_page <= max_pages:
            last_button_text = f"{transaction_page+1}/{max_pages}"
        else:
            last_button_text = None
        await MManager.content_surf(event=callback, state=state, bot=bot, content_unit=content,
                                    keyboard=trans_history_kb(page_list,
                                                              last_button_text=last_button_text),
                                    placeholder_text=placeholder_text)
    else:
        content: ContentUnit = await ContentUnit(tag="no_trans_history_send").get()
        placeholder_text = f"У вас пока нет транзакций :("
        await MManager.content_surf(event=callback, state=state, bot=bot, content_unit=content,
                                    keyboard=back_button(),
                                    placeholder_text=placeholder_text)

