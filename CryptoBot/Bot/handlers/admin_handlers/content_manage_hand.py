from aiogram import Router, Bot, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from Bot.keyboards.admin_keys import a_content_manage_main_kb, content_edit_kb, content_new_kb, admin_approve
from Bot.states.admin_states import AdminState
from Bot.utilts.mmanager import MManager
from Dao.models.bot_models import ContentUnit

router = Router()


@router.callback_query(F.data == "return", StateFilter(AdminState.content_remove,
                                                       AdminState.content_update))
@router.callback_query(F.data == "mnj_content", StateFilter(AdminState.main))
async def content_managing_starr(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await state.set_state(AdminState.content_select)
    msg = await bot.edit_message_text(
        "Это меню для управления сообщениями бота. Здесь вы можете поменять текст и медиа "
        "конкретного сообщения, если вы знаете его тэг. Если вы не знаете никаких тэгов, "
        "то не расстраивайтесь, тут же вы можете получить их полный список.\n\n"
        "- Пришлите тег, чтобы работать с имеющимся по нему сообщением, или добавить новое.",
        chat_id=callback.message.chat.id, message_id=callback.message.message_id,
        reply_markup=a_content_manage_main_kb())
    await MManager.sticker_store(state, sticker_message=msg)


@router.callback_query(F.data == "return", StateFilter(AdminState.content_update))
@router.callback_query(F.data == "all_tags", StateFilter(AdminState.content_select))
async def content_all_tags(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await callback.answer()
    tags = await ContentUnit.get_all_tags()
    if tags:
        text = "Ниже приведен список всех имеющихся в боте тэгов:\n\n"
        text += '<code>' + "</code>\n<code>".join(tags) + '</code>'
    else:
        text = "На данный момент в боте нет ни одного тэга"
    msg = await callback.message.answer(text)
    await MManager.garbage_store(state, msg.message_id)
    await MManager.sticker_surf(state, bot, callback.message.chat.id,
                                new_text="Чтобы начать работу с любым тегом, даже новым, просто пришлите его в чат:",
                                keyboard=a_content_manage_main_kb())


@router.message(StateFilter(AdminState.content_select))
@MManager.garbage_manage()
async def content_tag_selected(message: Message, state: FSMContext, bot: Bot):
    content = await ContentUnit(tag=message.text).get()
    await state.update_data(tag_use=message.text)
    if content.text or content.media_id:
        garb = await message.answer(f"Ниже приведено сообщение, найденное по тегу {message.text}")
        await MManager.garbage_store(state, garb.message_id)
        await MManager.content_surf(message, state, bot, content, keyboard=content_edit_kb())
    else:
        await MManager.sticker_surf(state, bot, message.chat.id,
                                    new_text=f"По тегу {message.text} не найдено сообщений. Желаете добавить?",
                                    keyboard=content_new_kb())


@router.callback_query(F.data == "edit", StateFilter(AdminState.content_select))
async def content_add(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await callback.answer()
    await bot.edit_message_reply_markup(chat_id=callback.message.chat.id, message_id=callback.message.message_id)
    await state.set_state(AdminState.content_update)
    tag = (await state.get_data()).get("tag_use")
    garb = await callback.message.answer(f"Отправьте сообщение, которое хотели бы видеть по тегу {tag}")
    await MManager.garbage_store(state, garb.message_id)


@router.message(StateFilter(AdminState.content_update))
@MManager.garbage_manage()
async def content_tag_selected(message: Message, state: FSMContext, bot: Bot):
    media_id = None
    media_type = None
    tag = (await state.get_data()).get("tag_use")
    state_dict = dict()
    if message.photo:
        media_id = message.photo[-1].file_id
        media_type = 'photo'
    elif message.video:
        media_id = message.video.file_id
        media_type = 'video'
    if media_id and media_type:
        state_dict.update(media_id=media_id, media_type=media_type)
    text = message.html_text if message.html_text else None
    if text:
        state_dict.update(text=text)

    content = ContentUnit(tag=tag, media_id=media_id, media_type=media_type, text=text)
    await state.update_data(state_dict)

    garb = await message.answer(f"Ниже отправлено текущее сообщение по тегу {tag}. Подтвердите его изменение в базе:")
    await MManager.garbage_store(state, garb.message_id)
    await MManager.content_surf(message, state, bot, content, keyboard=admin_approve())


@router.callback_query(F.data == "CONFIRM", StateFilter(AdminState.content_update))
async def content_add(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    tag = data.get("tag_use")
    media_id = data.get("media_id")
    media_type = data.get("media_type")
    text = data.get("text")
    content = ContentUnit(tag=tag, media_id=media_id, media_type=media_type, text=text)
    await content.add()
    await state.set_state(AdminState.content_select)
    await MManager.sticker_surf(state, bot, callback.message.chat.id,
                                new_text=f"Обновление сообщеения по тегу {tag} успешно завершено.\n\n"
                                         f"Вы можете продолжить работу с тегами, прислав другой или новый.",
                                keyboard=a_content_manage_main_kb())


@router.callback_query(F.data == "delete", StateFilter(AdminState.content_select))
async def content_add(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await state.set_state(AdminState.content_remove)
    tag = (await state.get_data()).get("tag_use")
    await MManager.sticker_surf(state, bot, callback.message.chat.id,
                                new_text=f"Вы собираетесь удалить сообщение по тегу {tag}.\n"
                                         f"Если оно используется в боте, вместо него будет использована заглушка.\n\n"
                                         f"Вы подтверждаете удаление?",
                                keyboard=admin_approve())


@router.callback_query(F.data == "CONFIRM", StateFilter(AdminState.content_remove))
async def content_add(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    tag = data.get("tag_use")
    media_id = data.get("media_id")
    media_type = data.get("media_type")
    text = data.get("text")
    content = ContentUnit(tag=tag, media_id=media_id, media_type=media_type, text=text)
    await content.delete()
    await state.set_state(AdminState.content_select)
    await MManager.sticker_surf(state, bot, callback.message.chat.id,
                                new_text=f"Сообщение по тегу {tag} успешно удалено.\n\n"
                                         f"Вы можете продолжить работу с тегами, прислав другой или новый.",
                                keyboard=a_content_manage_main_kb())