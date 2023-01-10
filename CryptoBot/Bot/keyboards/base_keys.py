from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def rep_back_button(some_kb_func):
    def wrap(*args, **kwargs):
        text = '⬅️ Назад'
        keyboard = some_kb_func(*args, **kwargs)
        if isinstance(keyboard, ReplyKeyboardBuilder):
            keyboard.row((KeyboardButton(text=text)))
            return keyboard.as_markup()
        elif isinstance(keyboard, ReplyKeyboardMarkup):
            keyboard.keyboard.append([KeyboardButton(text=text)])
        return keyboard

    return wrap
