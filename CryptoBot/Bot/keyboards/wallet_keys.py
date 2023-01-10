from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from Bot.keyboards.base_keys import rep_back_button
from Bot.utilts.currency_helper import base_tokens
from Dao.models.Token import Token


def main_wallet_keys():
    mark = InlineKeyboardBuilder()
    mark.row((InlineKeyboardButton(text=f"↙️ Пополнить", callback_data="replenish")))
    mark.row((InlineKeyboardButton(text=f"↗️ Отправить", callback_data="send")))
    mark.row((InlineKeyboardButton(text=f"🔄 Обменять", callback_data="exchange")))
    mark.row((InlineKeyboardButton(text=f"📆 История операций", callback_data="full_history")))
    # mark.row((InlineKeyboardButton(text=f"Обновить кошелек", callback_data="refresh_wallet_edit")))
    mark.adjust(2, 1, 1)
    return mark.as_markup(resize_keyboard=True)


def add_token_kb(custom_token_list: list | None = None):
    mark = InlineKeyboardBuilder()
    token_names = [token.token_name for token in custom_token_list]
    for token_name in set(token_names):
        mark.row((InlineKeyboardButton(text=f"{token_name}", callback_data=f"new_t_{token_name}")))
    mark.adjust(2)
    mark.row((InlineKeyboardButton(text="<< Назад", callback_data="refresh_wallet")))
    return mark.as_markup(resize_keyboard=True)


def delete_token_kb(token_list: list):
    mark = InlineKeyboardBuilder()
    for token in token_list:
        mark.row((InlineKeyboardButton(text=f"🔘 {token}", callback_data=f"del_t_{token}")))
    mark.adjust(2)
    mark.row((InlineKeyboardButton(text=f"↖️ Вернуться", callback_data="back_to_wall")))
    return mark.as_markup(resize_keyboard=True)


def inspect_token_kb(token_list: list[Token]):
    mark = InlineKeyboardBuilder()
    for token in token_list:
        mark.row((InlineKeyboardButton(text=f"🔘 {str(token)}", callback_data=f"inspect_t_{token}")))
    mark.adjust(2)
    mark.row((InlineKeyboardButton(text=f"↖️ Вернуться", callback_data="back_to_wall")))
    return mark.as_markup(resize_keyboard=True)


def network_kb(custom_network_list: list | None = None):
    mark = InlineKeyboardBuilder()
    algo_names = [algo.name for algo in custom_network_list]
    for algo_name in set(algo_names):
        mark.row((InlineKeyboardButton(text=f"{algo_name}", callback_data=f"new_n_{algo_name}")))
    mark.adjust(2)
    mark.row((InlineKeyboardButton(text="<< Назад", callback_data="back")))
    return mark.as_markup(resize_keyboard=True)


def addresses_kb(addresses_dict: dict, new_button: bool = True):
    mark = InlineKeyboardBuilder()
    for i in addresses_dict:
        mark.row((InlineKeyboardButton(text=str(i), callback_data=str(i))))
    mark.adjust(2)
    if new_button:
        mark.row((InlineKeyboardButton(text=f"➕ Создать еще кошелек", callback_data="new_address")))
    mark.row((InlineKeyboardButton(text=f"Назад", callback_data="back")))
    return mark.as_markup(resize_keyboard=True)


def refresh_button():
    mark = InlineKeyboardBuilder()
    mark.row((InlineKeyboardButton(text=f"🔄 Обновить кошелек", callback_data="refresh_wallet_keep")))
    return mark.as_markup(resize_keyboard=True)


def wallet_view_kb():
    mark = InlineKeyboardBuilder()
    mark.row((InlineKeyboardButton(text=f"📲 Показать QR код", callback_data="QRFK")))
    mark.add((InlineKeyboardButton(text=f"🖍 Изменить название", callback_data="rename_wallet")))
    mark.row((InlineKeyboardButton(text=f"📥 Мои адреса", callback_data="my_adresses")))
    mark.row((InlineKeyboardButton(text=f"📆 История зачислений", callback_data="receiving_address_history")))
    mark.row((InlineKeyboardButton(text=f"< Назад", callback_data="back")))
    mark.row((InlineKeyboardButton(text=f"<<< Назад в меню", callback_data="refresh_wallet")))
    return mark.as_markup(resize_keyboard=True)


def confirm_delete_kb():
    mark = InlineKeyboardBuilder()
    mark.add((InlineKeyboardButton(text=f"⭕️ Отменить", callback_data="back_to_wall")))
    mark.add((InlineKeyboardButton(text=f"♻️ Другой токен", callback_data="back")))
    mark.row((InlineKeyboardButton(text=f"🗑 Подтвердить удаление", callback_data="сonfirm_delete")))
    return mark.as_markup(resize_keyboard=True)


def currency_kb():
    mark = InlineKeyboardBuilder()
    for currency in base_tokens:
        chain = base_tokens[currency]
        mark.row((InlineKeyboardButton(text=f"🔘 {currency} [{chain}]",
                                       callback_data=chain)))
    return mark.as_markup(resize_keyboard=True)


@rep_back_button
def AML_menu():
    mark = ReplyKeyboardBuilder()
    return mark.as_markup(resize_keyboard=True)


def send_money_kb(token_list: list[str]):
    mark = InlineKeyboardBuilder()
    for token in set(token_list):
        mark.row((InlineKeyboardButton(text=f"{token}", callback_data=token)))
    return mark.as_markup(resize_keyboard=True)


def trans_history_start():
    mark = InlineKeyboardBuilder()
    mark.row((InlineKeyboardButton(text=f"История пополнений", callback_data="receiving_history")))
    mark.row((InlineKeyboardButton(text=f"История отправок", callback_data="sending_history")))
    mark.row((InlineKeyboardButton(text=f"История переводов по UID", callback_data="uid_history")))
    mark.row((InlineKeyboardButton(text=f"Назад", callback_data="refresh_wallet")))
    return mark.as_markup(resize_keyboard=True)
