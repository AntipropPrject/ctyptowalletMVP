from contextlib import suppress

from aiogram.types import User
from sqlalchemy.exc import IntegrityError

from Bot.exeptions.wallet_ex import DuplicateToken
from Bot.utilts.currency_helper import base_tokens
from Dao.DB_Postgres.session import create_session
from Dao.models.Owner import Owner
from Dao.models.Token import Token
from Services.token_service import TokenService


class OwnerService:

    @staticmethod
    async def get_wallets(user_id: int):
        session_connect = await create_session()
        async with session_connect() as session:
            owner: Owner = await session.get(Owner, str(user_id))
            return owner.wallets

    @staticmethod
    async def get_tokens(user_id: int):
        all_tokens = list()
        session_connect = await create_session()
        async with session_connect() as session:
            owner: Owner = await session.get(Owner, str(user_id))
            wallets = owner.wallets
            for wallet in wallets:
                wallet_obj = wallets[wallet]
                for address in wallet_obj.addresses:
                    address_obj = wallet_obj.addresses[address]
                    all_tokens = all_tokens + address_obj.tokens
        return all_tokens

    @staticmethod
    async def add_currency(user: User, token: str, network: str):
        session_connect = await create_session()
        async with session_connect() as session:
            token_ref = base_tokens.get(token)

            address = await Owner.get_address(session, user, token_ref['blockchain'])
            token_obj = await TokenService.get_token(base_tokens[token]['contract_address'])
            if not token:
                token_obj = Token(token_name=token,
                                  contract_Id=base_tokens[token]['contract_address'],
                                  network=network)
            if token_obj not in address.tokens:
                address.tokens.append(token_obj)
                session.add(address)
                with suppress(IntegrityError):
                    await session.commit()
            else:
                raise DuplicateToken
