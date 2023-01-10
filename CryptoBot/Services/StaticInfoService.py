from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from AllLogs.bot_logger import main_logger
from Dao.DB_Postgres.session import AlchemyMaster
from Dao.models import Blockchain, Algorithm
from Dao.models.Network import Network
from Dao.models.Token import Token
from _config.currency_data import StaticCurrency


class StaticInfoService:

    @staticmethod
    @AlchemyMaster.alchemy_session
    async def fill_bases(alchemy_session: AsyncSession):
        try:
            sttc_blockchains = StaticCurrency.blockchains
            for blockchain_name in sttc_blockchains:
                blockchain = Blockchain(name=blockchain_name)
                alchemy_session.add(blockchain)
                await alchemy_session.commit()
                tokens = sttc_blockchains[blockchain_name].get('tokens')
                for token in tokens:

                    contract = token['contract_address']
                    network_dict = token['network']
                    network_name = network_dict['name']
                    network_net = network_dict['mainnet']
                    network = Network(name=network_name, blockchain=blockchain_name, mainnet=network_net)
                    algorithm_name = token['algorithm']
                    algorithm = Algorithm(name=algorithm_name, blockchain=blockchain_name)

                    token = Token(token_name=token['name'], contract_Id=contract, network=network, algorithm=algorithm)
                    await alchemy_session.merge(token)
            await alchemy_session.commit()
        except IntegrityError:
            main_logger.infolog.info("Bases already populated, skipping filling up phase")
        else:
            main_logger.infolog.info("Bases was not populated, now filled with static info.")



    # @staticmethod
    # async def form_base_token(name: str):  # Изменить метод, когда улучшится хранилище базовых токенов
    #     """
    #     Checks base token library and search for token with given name
    #
    #     :return Token
    #     """
    #     token_dict = base_tokens.get(name)
    #     network = token_dict.get("network")[0]
    #     if DEBUG_MODE == True:
    #         contract_string = token_dict.get('testnet_contract_address')
    #     else:
    #         contract_string = token_dict.get('contract_address')
    #     return Token(contract_Id=contract_string, token_name=name, network=network)
    #
    # @staticmethod
    # async def fill_base():
    #     session_connect = await AlchemyMaster.create_session()
    #     async with session_connect() as session:
    #         for raw_token in base_tokens:
    #             token = await TokenService.form_base_token(raw_token)
    #             tokens = await TokenService.all_tokens()
    #             if token not in tokens:
    #                 session.add(token)
    #         with suppress(IntegrityError):
    #             await session.commit()
