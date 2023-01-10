from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message

from _config.variables import Data


async def loader(message: Message, chait_id: int, stage: int, text: str):
    bot = Data.main_bot
    if stage == 7:
        await bot.delete_message(chait_id, message.message_id)
    else:
        loader_bar = ['🟩', '⬜', '⬜', '⬜', '⬜', '⬜️']
        for i in range(stage):
            loader_bar[i] = '🟩'
        final_text = text + '\n\n' + ''.join(loader_bar)
        try:
            await bot.edit_message_text(final_text, chat_id=chait_id, message_id=message.message_id)
        except TelegramBadRequest:
            print('Не нашел message')
