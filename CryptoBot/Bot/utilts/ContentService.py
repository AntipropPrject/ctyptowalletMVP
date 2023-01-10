from contextlib import suppress

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardMarkup, InputMedia

from _config.settings import content_warn
from Dao.models.bot_models import ContentUnit


class ContentService:

    @staticmethod
    async def send(content: ContentUnit,
                   bot: Bot,
                   chat_id: int,
                   keyboard: InlineKeyboardMarkup | None = None,
                   placeholder_text: str | None = None):
        n_msg = None

        if not content.text:
            content.text = placeholder_text
            if not content.media_id and content_warn:
                content.text = f"<i>Bad content:</i>\n<code>{content.tag}</code>\n\n" + content.text
        text = content.formatted_text()
        if content.media_id:
            try:
                if content.media_type == 'video':
                    n_msg = await bot.send_video(chat_id=chat_id,
                                                 video=content.media_id,
                                                 caption=text,
                                                 reply_markup=keyboard)
                elif content.media_type == 'photo':
                    n_msg = await bot.send_photo(chat_id=chat_id,
                                                 photo=content.media_id,
                                                 caption=text,
                                                 reply_markup=keyboard)
                elif content.media_type == 'animation':
                    n_msg = await bot.send_animation(chat_id=chat_id,
                                                 animation=content.media_id,
                                                 caption=text,
                                                 reply_markup=keyboard)
            except TelegramBadRequest:
                n_msg = await bot.send_message(text=f"<i>BAD {content.media_type.upper()}</i>!\n"
                                                    f"<code>{content.tag}</code>\n\n" + text,
                                               chat_id=chat_id,
                                               reply_markup=keyboard)
        elif content.text:
            n_msg = await bot.send_message(text=text,
                                           chat_id=chat_id,
                                           reply_markup=keyboard)
        else:
            with suppress(TelegramBadRequest):
                n_msg = await bot.send_message(text=text,
                                           chat_id=chat_id,
                                           reply_markup=keyboard)
        return n_msg

    @staticmethod
    async def edit(content: ContentUnit,
                   bot: Bot,
                   chat_id: int,
                   target_msg_id: int,
                   keyboard: InlineKeyboardMarkup,
                   placeholder_text: str | None = None):
        n_msg = None

        if not content.text:
            content.text = placeholder_text
            if not content.media_id and content_warn:
                content.text = f"<i>Bad content:</i>\n<code>{content.tag}</code>\n\n" + content.text
        text = content.formatted_text()

        if content.media_id:
            try:
                n_msg = await bot.edit_message_media(media=InputMedia(type=content.media_type,
                                                                  media=content.media_id,
                                                                  caption=text),
                                                 chat_id=chat_id,
                                                 message_id=target_msg_id,
                                                 reply_markup=keyboard)
            except TelegramBadRequest:
                n_msg = await ContentService.send(content, bot, chat_id, keyboard, placeholder_text)
                await bot.delete_message(chat_id, target_msg_id)
        else:
            if not content.text:
                if content_warn:
                    text = f"<i>Bad content:</i>\n<code>{content.tag}</code>\n\n" + text

            with suppress(TelegramBadRequest):
                n_msg = await bot.edit_message_text(text=text,
                                                    chat_id=chat_id,
                                                    message_id=target_msg_id,
                                                    reply_markup=keyboard)
        return n_msg
