from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from Dao.models.Transaction import Transaction


def trans_history_kb(transactions_list: list[Transaction], last_button_text = str()):
    mark = InlineKeyboardBuilder()
    for transaction in transactions_list:
        t_type = 'Отправка' if transaction.type == 'sending' else 'Зачисление'

        if transaction.status == 'SUCCESS':
            stts = '✅'
        elif transaction.status == 'FAILED':
            stts = '🅾️'
        else:
            stts = '🔄'

        text = f'{stts} || {transaction.datetime} {t_type} {transaction.amount} {transaction.token.token_name}'
        mark.row((InlineKeyboardButton(text=text, callback_data=f"trid_{transaction.id}")))
    if last_button_text:
        mark.row((InlineKeyboardButton(text=last_button_text, callback_data="next_page_tsend")))
    return mark.as_markup()
