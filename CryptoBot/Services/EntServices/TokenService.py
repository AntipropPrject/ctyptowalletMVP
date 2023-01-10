from collections import namedtuple
from contextlib import suppress

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from Bot.utilts.currency_helper import base_tokens
from _config.settings import DEBUG_MODE
from Dao.DB_Postgres.session import AlchemyMaster
from Dao.models.Network import Network
from Dao.models.Owner import Owner
from Dao.models.Token import Token


class TokenService:

    @staticmethod
    async def find_address_token(u_id: str, token_name: str, token_network: str, path_index: int = 0):
        """
        Method to get info about token and linked address for given user, token name, token network.

        Returns object with parameters "adress" (Address object) and "token" (Token object)
        """
        result = namedtuple("adress_token", "address token")
        session_connect = await AlchemyMaster.create_session()
        async with session_connect() as session:
            owner: Owner = await session.get(Owner, u_id)
            wallets = owner.wallets
            for wallet in wallets:
                wallet_obj = wallets[wallet]
                for address in wallet_obj.addresses:
                    address_obj = wallet_obj.addresses[address]
                    if address_obj.path_index == path_index:
                        for token in address_obj.tokens:
                            if token.network == token_network:
                                if token.token_name == token_name:
                                    return result(address_obj, token)
                            return result(address_obj, None)

    @staticmethod
    @AlchemyMaster.alchemy_session
    async def get_token(token_name: str, token_algorithm: str,
                        *,
                        main_net: bool = True, alchemy_session: AsyncSession) -> Token:
            query = select(Token).filter(Token.token_name == token_name, Token.algorithm_name == token_algorithm)
            result = (await alchemy_session.execute(query)).unique()
            if result:
                for raw in list(result):
                    token = raw[0]
                    if token.network.mainnet == main_net:
                        return token

    @staticmethod
    async def form_base_token(name: str):  # Изменить метод, когда улучшится хранилище базовых токенов
        """
        Checks base token library and search for token with given name

        :return Token
        """
        token_dict = base_tokens.get(name)
        network = token_dict.get("network")[0]
        if DEBUG_MODE == True:
            contract_string = token_dict.get('testnet_contract_address')
        else:
            contract_string = token_dict.get('contract_address')
        return Token(contract_Id=contract_string, token_name=name, network=network)

    @staticmethod
    async def fill_base():
        session_connect = await AlchemyMaster.create_session()
        async with session_connect() as session:
            for raw_token in base_tokens:
                token = await TokenService.form_base_token(raw_token)
                tokens = await TokenService.all_tokens()
                if token not in tokens:
                    session.add(token)
            with suppress(IntegrityError):
                await session.commit()

    @staticmethod
    async def all_tokens():
        session_connect = await AlchemyMaster.create_session()
        async with session_connect() as session:
            return [token[0] for token in list((await session.execute(select(Token))).unique())]


    @staticmethod
    @AlchemyMaster.alchemy_session
    async def tokens_for_network(network: str, *, alchemy_session: AsyncSession):
        session_connect = await AlchemyMaster.create_session()
        async with session_connect() as session:
            tokens = [token[0] for token in list(
                (await session.execute(select(Token).filter(Token.network == network))).unique()
            )]
            print(tokens)
        return tokens


    @staticmethod
    @AlchemyMaster.alchemy_session
    async def alorithms_for_token_name(token_name: str, alchemy_session: AsyncSession):
        tokens = list(
            (await alchemy_session.execute(select(Token).filter(Token.token_name == token_name))).unique()
        )
        algorithms = [token.algorithm for raw in tokens for token in raw]
        return algorithms


    @staticmethod
    @AlchemyMaster.alchemy_session
    async def tokens_for_blockchain(blockchain_name: str, alchemy_session: AsyncSession):
        query = select(Token).filter(Token.network.has(Network.blockchain == blockchain_name))
        result = list((await alchemy_session.execute(query)).unique())
        tokens = [raw[0] for raw in result]
        return tokens