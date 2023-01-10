from string import ascii_letters, digits

from Crypto.Random import random
from cryptography.hazmat.primitives import hashes
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from Dao.DB_Postgres.session import AlchemyMaster
from Dao.models.Address import Address
from Dao.models.Owner import Owner
from Dao.models.Wallet import Wallet


class OwnerService:

    @staticmethod
    async def register(password: str | None = None):
        """ For new users """
        session_connect = await AlchemyMaster.create_session()
        async with session_connect() as session:
            password = OwnerService._password_encode(password)
            uid = await OwnerService._form_uid()
            try:
                stmt = insert(Owner).values(id=uid, password=password)
                do_nothing = stmt.on_conflict_do_nothing(index_elements=['id'])
                await session.execute(do_nothing)
                await session.commit()
                return uid
            except IntegrityError:
                await session.rollback()
                raise

    @staticmethod
    async def _form_uid():
        session_connect = await AlchemyMaster.create_session()
        async with session_connect() as session:
            reform = True
            while reform:
                string = ascii_letters + digits
                result = ''.join((random.choice(string) for _ in range(7))).upper()
                reform = True if await session.get(Owner, result) else False
        return result

    @staticmethod
    def _password_encode(text: str):
        digest = hashes.Hash(hashes.SHA256())
        digest.update(bytes(text, "UTF-8"))
        result = digest.finalize()
        return str(result)

    @staticmethod
    async def password_check(session: AsyncSession, uid: str, password: str):
        owner: Owner = await session.get(Owner, uid)
        phash = OwnerService._password_encode(password)
        return True if owner.password == phash else False

    @staticmethod
    async def get_wallets(u_id: str):
        session_connect = await AlchemyMaster.create_session()
        async with session_connect() as session:
            owner: Owner = await session.get(Owner, u_id)
            return owner.wallets

    @staticmethod
    async def get_tokens(u_id: str):
        all_tokens = list()
        session_connect = await AlchemyMaster.create_session()
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
    async def get_chain_address(u_id: str, blockchain: str, path_index: int = 0):
        session_connect = await AlchemyMaster.create_session()
        async with session_connect() as session:
            address: Address = (await session.execute(
                select(Address).where(
                    Address.path_index == path_index, Address.wallet_id == select(Wallet.id).where(
                        Wallet.owner_id == u_id, Wallet.blockchain == blockchain).scalar_subquery()))
                                ).first()[0]
            return address

    @staticmethod
    async def get_all_chain_addresses(u_id: str, blockchain: str):
        session_connect = await AlchemyMaster.create_session()
        addresses_list = list()
        async with session_connect() as session:
            addresses = (await session.execute(
                select(Address).where(Address.wallet_id == select(Wallet.id).where(
                    Wallet.owner_id == u_id, Wallet.blockchain == blockchain).scalar_subquery()))
                       ).unique()
            for address in addresses:
                addresses_list.append(address[0])
            return addresses_list
