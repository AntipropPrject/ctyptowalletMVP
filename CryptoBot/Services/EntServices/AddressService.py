from contextlib import suppress

import requests
from Services.CryptoMakers.ETH.eth_maker import EthMaker
from Services.CryptoMakers.Tron.tron_maker import TronMaker
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from Bot.exeptions.wallet_ex import DuplicateToken
from Dao.DB_Postgres.session import AlchemyMaster
from Dao.models.Address import Address
from Dao.models.Owner import Owner
from Dao.models.Token import Token
from Dao.models.Transaction import Transaction
from Dao.models.Wallet import Wallet
from Services.CryptoMakers.Maker import Maker


class MakerFactory:
    @staticmethod
    def get_maker(token: Token) -> Maker:
        maker = None
        if token.network.blockchain == token.algorithm.blockchain:
            blockchain = token.network.blockchain
            if blockchain == "tron":
                maker = TronMaker()
            elif blockchain == "ethereum":
                maker = EthMaker()

            if maker:
                return maker
        else:
            raise Exception("Can't get maker for this token!\n"
                            f"net bc {token.network.blockchain}\n"
                            f"algo bc {token.algorithm.blockchain}"
                            f"token name {token.token_name}")



class AddressService:

    @staticmethod
    async def get_address_balances(address: str, specific: list[Token] | None = None):
        # TODO может быть переделать, получать из фабрики, вызывать только getBalance
        session_connect = await AlchemyMaster.create_session()
        async with session_connect() as session:
            address_obj: Address = await session.get(Address, address)
            balances = dict()

            for token in address_obj.tokens:
                if (specific and token in specific) or not specific:
                    b_maker = MakerFactory.get_maker(token)
                    await b_maker.init_client(address=address_obj, token=token)
                    balance = await b_maker.get_balance()
                    print("BALANCE", balance)

                    balances.update({token.token_name: balance})
        return balances

    @staticmethod
    def get_address_for_transaction(owner: Owner, blockchain_name: str, contract_id: str) -> Address or None:
        wallet: Wallet = owner.wallets[blockchain_name]
        addresses: list = wallet.addresses.values()
        for address in addresses:
            if contract_id in address.token_list:
                return address

    @staticmethod
    async def add_currency(address: str | Address, token: Token):
        session_connect = await AlchemyMaster.create_session()
        async with session_connect() as session:
            if isinstance(address, str):
                address: Address = await session.get(Address, address)

            token_exists: Token = await session.get(Token, token.contract_Id)
            if token_exists:
                token = token_exists

            if token not in address.tokens:
                address.tokens.append(token)
                session.add(address)
                with suppress(IntegrityError):
                    await session.commit()
            else:
                raise DuplicateToken

    @staticmethod
    async def remove_currency(address: str, contract_id: str):
        session_connect = await AlchemyMaster.create_session()
        async with session_connect() as session:
            address_obj: Address = await session.get(Address, address)
            token_obj: Token = await session.get(Token, contract_id)
            for ad_token in address_obj.tokens:
                if token_obj == ad_token:
                    address_obj.tokens.remove(ad_token)
                    session.add(address_obj)
                    await session.commit()

    @staticmethod
    async def get_address_transactions(address: Address) -> dict[str, Transaction]:

        # TODO: Судя по всему, это метод для получения транзакций на адресе через внешний сервис. Он не доделан.
        # Вероятно предполагается, что здесь будет использоваться фабрика мейкеров и какой-то метод внутри них.

        session = await AlchemyMaster.create_session()
        counter = 0
        resp = requests.get(
            f"https://apilist.tronscanapi.com/api/accountv2?address={address.address}&source=search&word=TQzqehsVt7UENiBXBWwHUwDF9GPWvhxyvA&session-id=590c839e-f6a8-458e-953c-2e183eb8e884&order=0")
        json_dict = resp.json()
        transactions_in: int = json_dict["transactions_in"]
        transactions: int = json_dict["transactions"]
        # add
        if not transactions_in == "0":
            with_price_tokens = json_dict["withPriceTokens"]
            for el in with_price_tokens:
                if el["tokenName"] == "USDT" and float(el["balance"]) > 0:
                    float_balance = float(el["balance"]) * 1_000_000
                    print(f"{float_balance}       {el['tokenName']}")
                    print(address.address)


    @staticmethod
    @AlchemyMaster.alchemy_session
    async def address_local_transactions(address: Address, *, alchemy_session: AsyncSession) -> list[Transaction]:
        query = select(Transaction).filter(Transaction.address.has(Address.address == address.address,
                                                                   Address.path_index == address.path_index))
        result = (await alchemy_session.execute(query)).unique()
        transaction_list = [raw[0] for raw in list(result)]
        return transaction_list
