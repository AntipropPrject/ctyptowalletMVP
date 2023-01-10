from aiogram import Router, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from requests import HTTPError
from sqlalchemy.ext.asyncio import AsyncSession

from Bot.filters.auth_filter import NotAuthFilter
from Bot.handlers.main_handlers.auth_hand import you_need_tb_authenticated
from Bot.handlers.main_handlers.main_menu_hand import title_entry_point
from Bot.keyboards.main_keys import main_menu_kb
# from Bot.utilts.USDT_Calculator import USDT_Calculator
from Bot.utilts.mmanager import MManager
from Dao.DB_Redis import DataRedis
from Dao.models.Address import Address
from Dao.models.Owner import Owner
from Dao.models.Token import Token
from Dao.models.Transaction import Transaction
from Dao.models.Wallet import Wallet
from Dao.models.bot_models import ContentUnit
from Services.CryptoMakers.address_gen import Wallet_web3
from Services.EntServices.TransactionService import TransactionService

router = Router()


# router.message.filter(F.from_user.id.in_(Data.superadmins))

@router.message(Command("start"))
@MManager.garbage_manage()
async def commands_start(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    await MManager.garbage_store(state, message.message_id)
    await MManager.purge_chat(bot, message_id=message.message_id, chat_id=message.chat.id)
    if await NotAuthFilter()(message):
        await you_need_tb_authenticated(message, state, bot)
    else:
        await title_entry_point(message, state, bot)


@router.message(Command("exit"))
@MManager.garbage_manage()
async def commands_exit(message: Message, state: FSMContext, bot: Bot):
    await DataRedis.log_off(message.from_user.id)
    await MManager.clean(state, bot, message.chat.id, deep=True)
    await state.clear()
    content: ContentUnit = await ContentUnit(tag="bye_bye").get()
    await MManager.content_surf(message, state, bot, content,
                                placeholder_text='Вы были разлогинены\n\nЖдем вас снова!')


@router.message(Command("generate"))
async def commands_start(message: Message, state: FSMContext, session: AsyncSession):
    owner: Owner = await session.get(Owner, message.from_user.id)
    wallet = await owner.createWallet(blockchain="tron", session=session)
    await message.answer(str(wallet), reply_markup=main_menu_kb())


@router.message(Command("getMyWallets"))
async def commands_start(message: Message, state: FSMContext, session: AsyncSession):
    owner: Owner = await session.get(Owner, str(message.from_user.id))
    print(owner.wallets)

    for key in owner.wallets:
        wallet: Wallet = owner.wallets[key]
        print(wallet.tokens)
        await message.answer(str(owner.wallets[key]), reply_markup=main_menu_kb())


@router.message(Command("getbalance"))
async def commands_start(message: Message, state: FSMContext, session: AsyncSession):
    owner: Owner = await session.get(Owner, str(message.from_user.id))
    print(owner.wallets)
    for key in owner.wallets:
        try:
            print(await owner.wallets[key].getBalance())
        except HTTPError as e:
            print(e)

        await message.answer(str(owner.wallets[key]), reply_markup=main_menu_kb())


@router.message(Command("createTransaction"))
async def commands_start(message: Message, state: FSMContext, session: AsyncSession):
    # owner: Owner = await session.get(Owner, str(message.from_user.id))

    owner: Owner = Owner(id="Kakcam",
                         username="wdwdwdwd")
    # owner.wallets["tron"] = Wallet(blockchain="tron")
    address: Address = Address(address="token_address")
    address.transactions["newTrans"] = Transaction(id=25,
                                                   token_contract_id="TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
                                                   from_wallet=address.address)
    owner.wallets["tron123"] = Wallet(blockchain="tron123")
    token: Token = Token(contract_Id="token_contract", token_name="token_name")
    print(type(address.tokens))
    address.tokens.append(token)
    wallet_tron: Wallet = owner.wallets["tron123"]
    wallet_tron.addresses[address.address] = address

    session.add(owner)
    await session.commit()
    await session.close()
    owner: Owner = await session.get(Owner, str(message.from_user.id))
    session.add(owner)
    await session.commit()
    await session.close()


@router.message(Command("test"))
async def ttt(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    u_id = await DataRedis.find_user(user_id)
    owner: Owner = await session.get(Owner, u_id)
    wallet = [owner.wallets[wallet] for wallet in owner.wallets if owner.wallets[wallet].blockchain == 'tron'][0]
    mnemonic = wallet.mnemonic
    await Wallet_web3().create_wallet(blockchain=wallet.blockchain, u_id=u_id, wallet_name='asd', mnemonic=mnemonic,
                                    path_index=3)
    trans_list = await TransactionService.get_user_transactions(u_id, transaction_type='sending')
    print(trans_list)


@router.message(Command("try"))
@MManager.garbage_manage(store=True, clean=True)
async def asd(message: Message, session: AsyncSession, state: FSMContext, bot: Bot):
    owner: Owner = await session.get(Owner, str(message.from_user.id))
    # query = """ INSERT INTO address_tokens VALUES ('token_address','TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t') """
    wallet = owner.wallets.get("tron")
    address = wallet.addresses.get("TTwG26XCBQZvu3Xdi8BXtsqKGGLQFdTnea")
    token_list = address.tokens
    print(f'token - {token_list[0].token_name}')
    transaction = await createTransaction(address=address,
                                                         amount=50,
                                                         token=token_list[0],
                                                         to_address="THMxwS8Rq21jVtySrjipD5rU5h32XDj51V")
    print(transaction)
