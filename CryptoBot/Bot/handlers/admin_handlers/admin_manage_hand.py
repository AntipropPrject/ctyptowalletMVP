from aiogram import Router, Bot, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.exc import IntegrityError

from Bot.keyboards.admin_keys import admin_manage_kb, admin_back, admin_approve
from Bot.states.admin_states import AdminState
from Bot.utilts.mmanager import MManager
from Dao.models.bot_models import Admin

router = Router()


@router.callback_query(F.data == "return", StateFilter(AdminState.admins_manage_add, AdminState.admins_manage_remove))
@router.callback_query(F.data == "mnj_admins", StateFilter(AdminState.main))
async def admin_manage(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await state.set_state(AdminState.admins_manage)
    await bot.edit_message_text("Здесь вы можете добавить или удалить администратора бота.",
                                chat_id=callback.message.chat.id, message_id=callback.message.message_id,
                                reply_markup=admin_manage_kb())


@router.callback_query(F.data == "addmin", StateFilter(AdminState.admins_manage))
async def admins_manage_add(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await state.set_state(AdminState.admins_manage_add)
    await bot.edit_message_text("Пришлите telegram_id человека, которого вы хотите назначить администратором:",
                                chat_id=callback.message.chat.id, message_id=callback.message.message_id,
                                reply_markup=admin_back())


@router.message(StateFilter(AdminState.admins_manage_add))
@MManager.garbage_manage()
async def admins_manage_add_use(message: Message, state: FSMContext, bot: Bot):
    if message.text.isdigit():
        await state.update_data(add_min_id=message.text)
        text = f"Вы хотите добавить в администраторы пользователя с telegram_id: <code>{message.text}</code>"
        keyboard = admin_approve()
    else:
        text = "Это не telegram_id. \n\nВы можете получить telegram_id в боте вроде этого: https://t.me/JsonDumpBot"
        keyboard = admin_back()
    await MManager.sticker_surf(state, bot, message.chat.id, new_text=text, keyboard=keyboard)


@router.callback_query(F.data == "CONFIRM", StateFilter(AdminState.admins_manage_add))
async def admins_manage_add_done(callback: CallbackQuery, state: FSMContext, bot: Bot):
    new_admin_id = int((await state.get_data()).get("add_min_id"))
    try:
        await Admin(telegram_id=new_admin_id).promote()
        text = f'Администратор <code>{new_admin_id}</code> успешно добавлен'
    except IntegrityError:
        text = 'Такой администратор уже есть!'
    await state.set_state(AdminState.admins_manage)
    await bot.edit_message_text(text, chat_id=callback.message.chat.id,
                                message_id=callback.message.message_id,
                                reply_markup=admin_manage_kb())


# TODO: Выдавать тут список администраторов
@router.callback_query(F.data == "remdmin", StateFilter(AdminState.admins_manage))
async def admins_manage_remove(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await state.set_state(AdminState.admins_manage_remove)
    await bot.edit_message_text("Пришлите telegram_id человека, которого вы убрать из администраторов:",
                                chat_id=callback.message.chat.id, message_id=callback.message.message_id,
                                reply_markup=admin_back())


@router.message(StateFilter(AdminState.admins_manage_remove))
@MManager.garbage_manage()
async def admins_manage_remove_use(message: Message, state: FSMContext, bot: Bot):
    if message.text.isdigit():
        if await Admin(telegram_id=int(message.text)).check():
            await state.update_data(add_min_id=message.text)
            text = f"Вы хотите удалить администратора с telegram_id: <code>{message.text}</code>"
            keyboard = admin_approve()
        else:
            text = f"Администратора с telegram_id <code>{message.text}</code> не существует!"
            keyboard = admin_back()
    else:
        text = "Это не telegram_id. \n\nВы можете получить telegram_id в боте вроде этого: https://t.me/JsonDumpBot"
        keyboard = admin_back()
    await MManager.sticker_surf(state, bot, message.chat.id, new_text=text, keyboard=keyboard)


@router.callback_query(F.data == "CONFIRM", StateFilter(AdminState.admins_manage_remove))
async def admins_manage_add_done(callback: CallbackQuery, state: FSMContext, bot: Bot):
    new_admin_id = int((await state.get_data()).get("add_min_id"))
    await Admin(telegram_id=new_admin_id).demote()
    text = f'Администратор <code>{new_admin_id}</code> успешно удален'
    await state.set_state(AdminState.admins_manage)
    await bot.edit_message_text(text, chat_id=callback.message.chat.id,
                                message_id=callback.message.message_id,
                                reply_markup=admin_manage_kb())
