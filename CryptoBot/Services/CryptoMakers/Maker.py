from Dao.models.Address import Address
from Dao.models.Token import Token
from Dao.models.Transaction import Transaction
from Services.CryptoMakers.schemas import ComissionStrategy


class Maker:

    async def init_client(self, transaction: Transaction = None, token: Token = None, address: Address = None):
        """
        accepts a transaction for transfers
        accepts the address and token to receive the balance
        """
        pass

    async def transfer(self, fee_strategy: str = "average") -> dict or None:  # ["slow": 1, "average": 1.5, "fast": 2]
        pass

    async def get_balance(self) -> float:
        pass

    async def comission_strategy(self, fee_strategy: str = "average") -> ComissionStrategy:
        pass
