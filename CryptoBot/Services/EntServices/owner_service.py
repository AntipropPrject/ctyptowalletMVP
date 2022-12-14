from contextlib import suppress

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from Bot.exeptions.wallet_ex import DuplicateToken
from Bot.utilts.currency_helper import base_tokens
from Bot.utilts.settings import DEBUG_MODE
from Dao.DB_Postgres.session import create_session
from Dao.models.Address import Address
from Dao.models.Owner import Owner
from Dao.models.Token import Token
from Dao.models.Wallet import Wallet
from Services.EntServices.TokenService import TokenService


class OwnerService:

    @staticmethod
    async def get_wallets(user_id: int):
        session_connect = await create_session()
        async with session_connect() as session:
            owner: Owner = await session.get(Owner, str(user_id))
            return owner.wallets

    @staticmethod
    async def get_tokens(u_id: str):
        all_tokens = list()
        session_connect = await create_session()
        async with session_connect() as session:
            owner: Owner = await session.get(Owner, u_id)
            wallets = owner.wallets
            for wallet in wallets:
                wallet_obj = wallets[wallet]
                for address in wallet_obj.addresses:
                    address_obj = wallet_obj.addresses[address]
                    all_tokens = all_tokens + address_obj.tokens
        return all_tokens

    @staticmethod
    async def add_currency(u_id: str, token: str, network: str):
        session_connect = await create_session()
        async with session_connect() as session:
            token_ref = base_tokens.get(token)

            address = await OwnerService.get_chain_address(u_id, token_ref['blockchain'])
            if DEBUG_MODE==True:
                contract_string = 'testnet_contract_address'
            if DEBUG_MODE == False:
                contract_string = 'contract_address'
            token_obj = await TokenService.get_token(base_tokens[token][contract_string])
            if not token_obj:
                token_obj = Token(token_name=token,
                                  contract_Id=base_tokens[token][contract_string],
                                  network=network)
            if token_obj not in address.tokens:
                address.tokens.append(token_obj)
                session.add(address)
                with suppress(IntegrityError):
                    await session.commit()
            else:
                raise DuplicateToken

    @staticmethod
    async def get_chain_address(u_id: str, blockchain: str, path_index: int = 0):
        session_connect = await create_session()
        async with session_connect() as session:
            address: Address = (await session.execute(
                select(Address).where(
                    Address.path_index == path_index, Address.wallet_id == select(Wallet.id).where(
                        Wallet.owner_id == u_id, Wallet.blockchain == blockchain).scalar_subquery()))
                                ).first()[0]
            print(address)
            return address
