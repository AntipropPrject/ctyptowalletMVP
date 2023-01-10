import json
import os
import math
from web3 import Web3, AsyncHTTPProvider
from web3.eth import AsyncEth
from web3.geth import Geth, AsyncGethTxPool, AsyncGethPersonal, AsyncGethAdmin
from web3.net import AsyncNet

from Dao.models import Token, Address
from Dao.models.Transaction import Transaction
from Services.CryptoMakers.Maker import Maker
from Services.CryptoMakers.schemas import ComissionStrategy

EIP20_ABI = json.loads(
    '[{"constant":true,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_from","type":"address"},{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transferFrom","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"anonymous":false,"inputs":[{"indexed":true,"name":"_from","type":"address"},{"indexed":true,"name":"_to","type":"address"},{"indexed":false,"name":"_value","type":"uint256"}],"name":"Transfer","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"_owner","type":"address"},{"indexed":true,"name":"_spender","type":"address"},{"indexed":false,"name":"_value","type":"uint256"}],"name":"Approval","type":"event"}]')  # noqa: 501


class EthMaker(Maker):

    def __init__(self):
        self.api_key = os.getenv('eth_API')
        self.network = None
        self._main_adds = os.getenv('eth_address')
        self._main_pk_key = os.getenv('eth_private_key')
        self.w3 = None

        self.transaction = None
        self.token = None
        self.address = None

        self.txn_resp = dict()
        self.eth_comission = None
        self.gas = None
        self.__BASE = 'https://{}.infura.io/v3/'

    async def init_client(self, transaction: Transaction = None, token: Token = None, address: Address = None):
        if transaction:
            self.transaction = transaction
            self.token = transaction.token
            self.address = transaction.address
        if token and address:
            self.token = token
            self.address = address

        base = self.__BASE
        base = base.format(self.token.network.name)
        self.__BASE = base

        self.w3 = Web3(
            AsyncHTTPProvider(self.__BASE + self.api_key),
            modules={'eth': (AsyncEth,),
                     'net': (AsyncNet,),
                     'geth': (Geth,
                              {'txpool': (AsyncGethTxPool,),
                               'personal': (AsyncGethPersonal,),
                               'admin': (AsyncGethAdmin,)})
                     },
            middlewares=[]  # See supported middleware section below for middleware options
        )

    async def gas_strategy(self, token: Token):
        if token.network.name in ["mainnet", "goerli"]:
            if token.token_name == "ETH":
                gas = 21000
            else:
                gas = 21000
        else:
            gas = 21000
        return gas

    async def comission_strategy(
            self,
            token: Token = None,
            com_strategy: ComissionStrategy = ComissionStrategy,
            fee_strategy: str = "average") -> ComissionStrategy:

        coefficients = {"slow": 1, "average": 1.5, "fast": 2}  # коэффициент умножения стоимости газа

        if fee_strategy not in coefficients:
            raise ValueError("Value <strategy> is incorrect")

        token = token if token else self.token

        if token is None:
            raise AttributeError("Token not defined")

        gas_price = await self.w3.eth.gas_price  # wei

        gas_price_x = int(gas_price * coefficients[fee_strategy])
        gas_amount = await self.gas_strategy(token)
        com_strategy.gas_price = gas_price_x
        com_strategy.gas_amount = gas_amount
        com_strategy.comission = int(gas_amount * gas_price_x)  # wei
        return com_strategy

    async def lending(self, fee_strategy: str):

        comission_strategy = await self.comission_strategy(fee_strategy=fee_strategy)

        nonce = await self.w3.eth.get_transaction_count(self._main_adds, 'pending')
        value = comission_strategy.comission + 300_000_000  # comission + 0,3 gwei
        self.txn_resp["network_fee"] = self.w3.from_wei(value, "ether")  # main token

        txn = {
            'chainId': await self.w3.eth.chain_id,
            'from': self._main_adds,
            'to': self.transaction.address.address,
            'value': value,
            'nonce': nonce,
            'gasPrice': comission_strategy.gas_price,
            'gas': comission_strategy.gas_amount + 2000,
        }
        try:
            try:
                signed_txn = self.w3.eth.account.sign_transaction(txn, self._main_pk_key)
            except ValueError:
                nonce += math.ceil(round(nonce / 8, 3))
                txn['nonce'] = nonce
                signed_txn = self.w3.eth.account.sign_transaction(txn, self._main_pk_key)

            await self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)  # хэш отправки с мейн кошелька
        except Exception as e:
            print(e)
            print("На основном кошельке недостаточно эфира для совершения транзакции")

    async def get_balance(self) -> float:
        contract = None if self.token.contract_Id == 'eth' else self.token.contract_Id

        if contract:
            contract = self.w3.eth.contract(contract, abi=EIP20_ABI)
            token_decimals_obj = contract.functions.decimals()
            balance_obj = contract.functions.balanceOf(self.address.address)

            decimals = await token_decimals_obj.call()
            balance_of_token = await balance_obj.call()
            balance = balance_of_token / 10 ** decimals
            return balance

        elif contract is None:
            balance = await self.w3.eth.get_balance(self.address.address)
            return float(self.w3.from_wei(balance, "ether"))

        else:
            raise ValueError("Could not find address")

    async def build_txn(self, nonce, fee_strategy: str) -> dict[str, int | str]:

        comission_strategy = await self.comission_strategy(fee_strategy=fee_strategy)
        self.txn_resp["network_fee"] = self.txn_resp.get("network_fee") + \
                                       self.w3.from_wei(comission_strategy.gas_amount, "ether")  # main token

        contract = self.token.contract_Id
        if contract is None:
            self.txn_resp["status"] = "Bilded"
            self.txn_resp["message"] = "transaction bilded"
            self.txn_resp["txn"] = None
            txn = {
                'chainId': await self.w3.eth.chain_id,
                'from': self.transaction.address.address,
                'to': self.transaction.foreign_address,
                'value': int(Web3.to_wei(self.transaction.amount, "ether")),
                'nonce': nonce,
                'gasPrice': comission_strategy.gas_price,
                'gas': comission_strategy.gas_amount,
            }
        else:
            contract = self.w3.eth.contract(contract, abi=EIP20_ABI)
            token_decimals = contract.functions.decimals()
            token_decimals = await token_decimals.call()

            reformat_amount = int(self.transaction.amount * 10 ** token_decimals)

            nonce = await self.w3.eth.get_transaction_count(self.transaction.address.address, 'pending')
            self.txn_resp["status"] = "Bilded"
            self.txn_resp["message"] = "transaction bilded"
            self.txn_resp["txn"] = None

            txn = await contract.functions.transfer(
                self.transaction.foreign_address, reformat_amount
            ).build_transaction({
                'chainId': await self.w3.eth.chain_id,
                'gasPrice': comission_strategy.gas_price,
                'gas': comission_strategy.gas_amount,
                'nonce': nonce,
            })
        return txn

    async def transfer(self, fee_strategy: str = "average"):

        await self.lending(fee_strategy)  # кредитование юзер кошелька

        nonce = await self.w3.eth.get_transaction_count(self.transaction.address.address, 'pending')

        trn = await self.build_txn(nonce, fee_strategy)

        try:
            address = self.transaction.address
            try:
                signed_txn = self.w3.eth.account.sign_transaction(trn, address.private_key)
                txn_hash = await self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            except ValueError:
                nonce += math.ceil(round(nonce / 8, 3))
                signed_txn = self.w3.eth.account.sign_transaction(trn, address.private_key)
                txn_hash = await self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            self.txn_resp["status"] = "SUCCESS"
            self.txn_resp["message"] = "Transfer success"
            self.txn_resp["txn"] = txn_hash.hex()

            # TODO CryptoBot/Bot/utilts/FunctionalService.py:45
            return self
        except ValueError:
            print("Баланса недостаточно для совершения транзакции")
