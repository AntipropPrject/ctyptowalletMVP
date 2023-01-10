from aiogram import Router, F, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from Bot.handlers.main_handlers.wallet_handlers import replenish_wallet_hand, tran_history_wallet_hand, send_wallet_hand
from Bot.keyboards.wallet_keys import main_wallet_keys
from Bot.states.main_states import MainState
from Bot.states.trans_states import Trs_transfer
from Bot.states.wallet_states import WalletStates
from Bot.utilts.mmanager import MManager
from Bot.utilts.pretty_texts import all_wallets_text
from Dao.DB_Redis import DataRedis
from Dao.models.bot_models import ContentUnit

router = Router()
router.include_router(replenish_wallet_hand.router)
router.include_router(send_wallet_hand.router)
router.include_router(tran_history_wallet_hand.router)
router.message.filter(StateFilter(MainState.welcome_state, WalletStates, Trs_transfer))


@router.callback_query(F.data.startswith('refresh_wallet'))
@MManager.garbage_manage(store=True, clean=True)
async def my_wallet_start(event: Message | CallbackQuery, state: FSMContext, bot: Bot):
    user_id = event.from_user.id
    u_id = await DataRedis.find_user(user_id)
    w_text = await all_wallets_text(u_id)
    content: ContentUnit = await ContentUnit(tag="wallet_text").get()
    content.add_formatting_vars(wallet_text=w_text, UID=u_id)
    message = event if isinstance(event, Message) else event.message

    await MManager.content_surf(event=message, state=state, bot=bot, content_unit=content,
                                keyboard=main_wallet_keys(),
                                placeholder_text=f"Кошелек пользователя {u_id}")

    await state.set_state(WalletStates.main)


@router.callback_query(F.data.startswith('back_to_wall'))
async def wallet_backing(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await state.set_state(WalletStates.main)
    text = await DataRedis.get_cached_text(callback.from_user.id, 'wallet')
    if not text:
        u_id = await DataRedis.find_user(callback.from_user.id)
        text = await all_wallets_text(u_id)
        await DataRedis.cache_text(callback.from_user.id, text, 'wallet')
    await bot.edit_message_text(text=text, chat_id=callback.message.chat.id,
                                message_id=callback.message.message_id, reply_markup=main_wallet_keys())
    await callback.answer()
