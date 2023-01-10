from aiogram.types import InlineKeyboardButton, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from Dao.models import Algorithm
from Dao.models.Token import Token


def m_transaction():
    mark = ReplyKeyboardBuilder()
    mark.row((KeyboardButton(text="🔄 Обменять")))
    mark.row((KeyboardButton(text="⤴️ Перевести")))
    mark.row((KeyboardButton(text="📝 История")))
    mark.row((KeyboardButton(text="⬅️ Назад")))
    mark.adjust(2, 1, 1, 1)
    return mark.as_markup(resize_keyboard=True)


def trans_token_kb(custom_token_list: list[Token]):
    mark = InlineKeyboardBuilder()
    token_names = [token.token_name for token in custom_token_list]
    for token_name in set(token_names):
        mark.row((InlineKeyboardButton(text=f"{token_name}", callback_data=f"tToken_{token_name}")))
    mark.adjust(2)
    mark.row((InlineKeyboardButton(text="<< Назад", callback_data="refresh_wallet")))
    return mark.as_markup(resize_keyboard=True)


def trans_network_kb(custom_network_list: list[Algorithm] | None = None):
    mark = InlineKeyboardBuilder()
    algo_names = [algo.name for algo in custom_network_list]
    for algo_name in set(algo_names):
        mark.row((InlineKeyboardButton(text=f"{algo_name}", callback_data=f"tAlgos_{algo_name}")))
    mark.adjust(2)
    mark.row((InlineKeyboardButton(text="<< Назад", callback_data="back")))
    return mark.as_markup(resize_keyboard=True)


def change_transfer_token():
    mark = InlineKeyboardBuilder()
    mark.row((InlineKeyboardButton(text="Изменить токен", callback_data="change_transfer_token")))
    return mark.as_markup(resize_keyboard=True)


def kb_confirm_transfer():
    mark = InlineKeyboardBuilder()
    mark.row((InlineKeyboardButton(text="✅ Подтвердить и отправить", callback_data="confirm_transfer_token")))
    mark.row((InlineKeyboardButton(text="🔄 Изменить сумму", callback_data="change_amount")))
    mark.row((InlineKeyboardButton(text="👨‍💼 Изменить получателя", callback_data="change_target")))
    mark.row((InlineKeyboardButton(text="<< Назад", callback_data="back")))
    return mark.as_markup(resize_keyboard=True)


def trans_result_keyboard():
    mark = InlineKeyboardBuilder()
    mark.row((InlineKeyboardButton(text="<< Назад в меню", callback_data="refresh_wallet")))
    mark.row((InlineKeyboardButton(text="📆 История транзакций", callback_data="full_history")))
    return mark.as_markup(resize_keyboard=True)
