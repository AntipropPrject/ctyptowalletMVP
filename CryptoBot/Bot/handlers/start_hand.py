import asyncio
import json

import requests
from aiogram import Router, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from requests import HTTPError
from sqlalchemy.ext.asyncio import AsyncSession

from Bot.filters.auth_filter import NotAuthFilter
from Bot.handlers.main_handlers.auth_hand import you_need_tb_authenticated
from Bot.handlers.main_handlers.main_menu_hand import main_menu
from Bot.keyboards.main_keys import main_menu_kb
# from Bot.utilts.USDT_Calculator import USDT_Calculator
from Bot.utilts.mmanager import MManager
from Dao.DB_Postgres.session import AlchemyMaster
from Dao.models.Address import Address
from Dao.models.Owner import Owner
from Dao.models.Token import Token
from Dao.models.Transaction import Transaction
from Dao.models.Wallet import Wallet
from Services.CryptoMakers.Tron.Tron_Maker import Tron_Maker
from Services.EntServices.AddressService import AddressService
from bata import Data

router = Router()


# router.message.filter(F.from_user.id.in_(Data.superadmins))

@router.message(Command("start"))
@MManager.garbage_manage()
async def commands_start(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    await MManager.garbage_store(state, message.message_id)
    await MManager.purge_chat(bot, message_id=message.message_id, chat_id=message.chat.id)
    if await NotAuthFilter()(message):
        await you_need_tb_authenticated(message, state)
    else:
        await main_menu(message, state, bot)


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
async def ttt(message: Message):
    session = await AlchemyMaster.create_session()
    async with session() as s:
        address: Address = await s.get(Address, "TFA3cwnVvj5HgeBGoQfYKjbKyYK6WgA7jQ")
        maker = Tron_Maker()
        await maker.request_transaction_history_from_tron_api(address)
        print(address.private_key)
        print(address.address)
        print(await address.public_fun())


@router.message(Command("try"))
@MManager.garbage_manage(store=True, clean=True)
async def asd(message: Message, session: AsyncSession, state: FSMContext, bot: Bot):
    owner: Owner = await session.get(Owner, str(message.from_user.id))
    # query = """ INSERT INTO address_tokens VALUES ('token_address','TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t') """
    wallet = owner.wallets.get("tron")
    address = wallet.addresses.get("TTwG26XCBQZvu3Xdi8BXtsqKGGLQFdTnea")
    token_list = address.tokens
    print(f'token - {token_list[0].token_name}')
    transaction = await AddressService.createTransaction(address=address,
                                                         amount=50,
                                                         token=token_list[0],
                                                         to_address="THMxwS8Rq21jVtySrjipD5rU5h32XDj51V")
    print(transaction)
