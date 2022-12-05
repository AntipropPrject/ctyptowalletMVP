from aiogram import Router, Bot, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from Bot.handlers.main_handlers.transaction_menu_hand import transaction_start
from Bot.handlers.main_handlers.wallet_hand import my_wallet_start
from Bot.keyboards.main_keys import main_menu_kb
from Bot.keyboards.wallet_keys import main_wallet_keys
from Bot.states.main_states import MainState
from Bot.states.trans_states import TransactionStates
from Bot.utilts.mmanager import MManager
from Dao.DB_Redis import DataRedis

router = Router()


async def main_menu(update: Message | CallbackQuery, state: FSMContext, bot: Bot):
    message = update if isinstance(update, Message) else update.message
    await MManager.clean(state, bot, message.chat.id)
    await state.clear()
    await state.set_state(MainState.welcome_state)
    bot_name = (await bot.get_me()).full_name
    u_id = await DataRedis.find_user(update.from_user.id)
    text = f'<b>👤 <code>{u_id}</code>, добро пожаловать в криптовалютный бот {bot_name}!</b>\n\nЧем я могу вам помочь?'
    try:
        await message.answer_photo("AgACAgIAAxkBAAICdGOKCDV-1-wERkVoojLvwO0ocCVdAALVwTEbxw5RSH90t1FwCJMUAQADAgADeAADKwQ",
                                   caption=text, reply_markup=main_menu_kb())
    except TelegramBadRequest:
        await message.answer(text, reply_markup=main_menu_kb())


@router.message(F.text == "💹 Мой кошелек")
async def menu_wallet_start(message: Message, bot: Bot, state: FSMContext, session: AsyncSession):
    await my_wallet_start(event=message, state=state, bot=bot, session=session)


@router.message(F.text == "👁‍🗨 AML Check")
async def menu_aml_start(message: Message, bot: Bot, state: FSMContext):
    stick_msg = await message.answer('AML проверка',
                                     reply_markup=main_wallet_keys())


@router.message(F.text == "↔️ Транзакции")
async def menu_transaction_start(message: Message, bot: Bot, state: FSMContext):
    await state.set_state(TransactionStates.main)
    await transaction_start(message, state)
