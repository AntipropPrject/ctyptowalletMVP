from aiogram import Router, Bot, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from Bot.filters.admin_filter import IsAdmin
from Bot.handlers.admin_handlers import admin_manage_hand, content_manage_hand
from Bot.keyboards.admin_keys import main_admin_kb
from Bot.states.admin_states import AdminState
from Bot.utilts.mmanager import MManager

router = Router()
router.include_router(admin_manage_hand.router)
router.include_router(content_manage_hand.router)


@router.message(Command("admin"), IsAdmin())
@MManager.garbage_manage()
async def admin_start(message: Message, state: FSMContext):
    await state.clear()
    await MManager.garbage_store(state, message.message_id)
    await state.set_state(AdminState.main)
    msg = await message.answer("Добро пожаловать в режим администрации!", reply_markup=main_admin_kb())
    await MManager.sticker_store(state, msg)


@router.callback_query(F.data == "return",
                       StateFilter(
                           AdminState.admins_manage,
                           AdminState.content_select
                       ))
async def admin_return(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await MManager.clean(state, bot, callback.message.chat.id)
    await state.clear()
    await state.set_state(AdminState.main)
    msg = await bot.edit_message_text("Это главное меню режима администрации.", chat_id=callback.message.chat.id,
                                      message_id=callback.message.message_id, reply_markup=main_admin_kb())
    await MManager.sticker_store(state, msg)


@router.callback_query(F.data == "exit", StateFilter(AdminState))
async def admin_exit(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await callback.answer()
    await bot.edit_message_text("Вы покинули режим администрации. Вы можете восстановить работу с ботом стандартной "
                                "командой /start", chat_id=callback.message.chat.id,
                                message_id=callback.message.message_id)
    await MManager.clean(state, bot, callback.message.chat.id)
    await state.clear()
