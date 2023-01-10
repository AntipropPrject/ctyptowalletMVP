import os

from httpx import AsyncClient, Timeout
from tronpy import AsyncTron
from tronpy.defaults import CONF_NILE
from tronpy.exceptions import BadAddress, AddressNotFound, ValidationError, UnknownError
from tronpy.keys import PrivateKey
from tronpy.providers import AsyncHTTPProvider

from _config.settings import STAKE_MODE
from Dao.models import Token
from Dao.models.Address import Address
from Dao.models.Transaction import Transaction
from Services.CryptoMakers.Maker import Maker
from Services.CryptoMakers.schemas import ComissionStrategy


class TronMaker(Maker):
    def __init__(self):
        self.api_key = os.getenv('tron_API')
        self._main_pk_key = os.getenv('main_private_key')
        self._main_adds = os.getenv('main_address')
        self._user_pk_key = None
        self._user_adds = None
        self.txn_resp = dict()

        self.transaction = None
        self.token = None
        self.address = None

        self.energy = 15000
        self.bandwitch = 1000
        self.trx_min_balance = 10
        self.TRON_SCAN_API_URL = "https://apilist.tronscanapi.com/api"
        self._fee_limit = 20_000_000

    async def init_client(self, transaction: Transaction = None, token: Token = None, address: Address = None):
        if transaction:
            self.transaction = transaction
            self.token = transaction.token
            self.address = transaction.address
        if token and address:
            self.token = token
            self.address = address

    def get_client(self):

        if self.token.network.name == "mainnet":
            return AsyncTron(provider=AsyncHTTPProvider(api_key=self.api_key, timeout=30))
        elif self.token.network.name == "nile":
            _http_client = AsyncClient(timeout=Timeout(timeout=30, connect=5, read=5))
            provider = AsyncHTTPProvider(CONF_NILE, client=_http_client)
            return AsyncTron(provider=provider)

        else:
            raise ValueError(f"network: <{self.token.network.name}>  not supported")

    async def account_resource(self):

        async with self.get_client() as client:
            account_resource = await client.get_account_resource(self.transaction.address.address)
            energy_used = account_resource.get("EnergyUsed", 0)
            energy_limit = account_resource.get("EnergyLimit", 0)
            remainde_energy_used = energy_limit - energy_used

            free_net_limit = account_resource.get("freeNetLimit", 0)
            free_net_used = account_resource.get("freeNetUsed", 0)
            remainder_free_net_used = free_net_limit - free_net_used

            net_used = account_resource.get("NetUsed", 0)
            net_limit = account_resource.get("NetLimit", 0)

            remainder_net_used = net_limit - net_used
            bandwitch = remainder_free_net_used + remainder_net_used

            return {
                "ENERGY": remainde_energy_used,
                "BANDWITCH": bandwitch
            }

    async def is_valid_address(self, address: str) -> bool:
        try:
            async with self.get_client() as client:
                return client.is_address(address)
        except ValueError:
            return False

    async def is_valid_contract(self, contract_address: str) -> str | bool:
        async with self.get_client() as client:
            try:
                contract = await client.get_contract(contract_address)
                return contract.name
            except BadAddress:
                return False

    async def freeze(self, amount: float, resource: str = "ENERGY"):
        print("Заморозка трх")
        async with self.get_client() as client:
            txb = client.trx.freeze_balance(
                owner=self._main_adds,
                amount=int(amount * 1_000_000),
                resource=resource,
                receiver=self.address.address
            )

            try:
                tx = await txb.build()
                p_key = PrivateKey(bytes.fromhex(self._main_pk_key))
                txn_ret = await tx.sign(p_key).broadcast()
                self.txn_resp["txn"] = await txn_ret.wait()
            except Exception as e:
                print(e)
            self.txn_resp["status"] = "ERROR"
            self.txn_resp["message"] = "Freeze failed"

    async def unfreeze(self, resource: str = "ENERGY"):

        async with self.get_client() as client:
            txb = client.trx.unfreeze_balance(
                owner=self._main_adds,
                resource=resource,
                receiver=self.address.address
            )
        try:
            tx = await txb.build()
            p_key = PrivateKey(bytes.fromhex(self._main_pk_key))
            txn_ret = await tx.sign(p_key).broadcast()
            self.txn_resp["txn"] = await txn_ret.wait()
        except Exception as e:
            print(e)
            self.txn_resp["status"] = "ERROR"
            self.txn_resp["message"] = "Unfreeze failed"

    async def get_balance(self) -> float:

        async with self.get_client() as client:
            contract = self.token.contract_Id
            try:
                if contract:
                    contract = await client.get_contract(contract)
                    return float(await contract.functions.balanceOf(self.address.address) / 1_000_000)

                else:
                    return float(await client.get_account_balance(self.address.address))
            except AddressNotFound:
                return float(0)

    async def comission_strategy(
            self,
            token: Token = None,
            com_strategy: ComissionStrategy = ComissionStrategy,
            fee_strategy: str = "average") -> ComissionStrategy:
        pass

    async def transfer(self, fee_strategy: str = "average"):
        f = fee_strategy
        address = self.transaction.address

        p_key = PrivateKey(bytes.fromhex(address.private_key))
        contract = self.transaction.token.contract_Id
        async with self.get_client() as client:

            if self.token.algorithm_name == "TRC-20" and self.token.contract_Id:
                contract_f = await client.get_contract(contract)
                txb = await contract_f.functions.transfer(
                    self.transaction.foreign_address,
                    int(self.transaction.amount * 1_000_000))
                txb = txb.with_owner(address.address).fee_limit(self._fee_limit)
            elif self.token.contract_Id is None:
                txb = (
                    client.trx.transfer(address.address, self.transaction.foreign_address,
                                        int(self.transaction.amount * 1_000_000))
                    .with_owner(address.address)
                    .fee_limit(self._fee_limit)
                )
            else:
                raise

            try:
                tx = await txb.build()
                txn_ret = await tx.sign(p_key).broadcast()
                self.txn_resp["status"] = "SUCCESS"
                self.txn_resp["message"] = "Transfer success"
                txn = await txn_ret.wait()
                self.txn_resp["txn"] = txn.get("id")
            except ValidationError:
                self.txn_resp["status"] = "ValidationError"
                self.txn_resp["message"] = "Account not active"
                self.txn_resp["txn"] = None
                await self.employer()
            except UnknownError:
                self.txn_resp["status"] = "BANDWITH_ERROR"
                self.txn_resp["message"] = "Energy or trx is not enough to transfer"
                self.txn_resp["txn"] = None
                await self.employer()
            return self

    async def employer(self):

        txn_info = self.txn_resp

        if txn_info.get("status") == "ValidationError":
            self.txn_resp["status"] = "ActivateAccount"
            self.txn_resp["message"] = "account in the process of activation"
            print(f"Аккаунт не активирован, выполняeтся перевод 1 TRX на адрес {self._user_adds}")
            await self.activate_account()

        elif txn_info.get("status") == "BANDWITH_ERROR":
            self.txn_resp["status"] = "BandwitchError"

            if STAKE_MODE is True:
                account_resource = await self.account_resource()
                print("account_resource", account_resource)
                energy = account_resource.get("ENERGY")
                bandwitch = account_resource.get("BANDWITCH")
                print('account_resource', account_resource)
                if energy < self.energy:
                    print("На балансе недостаточно ENERGY, выполняется процесс пополнения ENERGY")
                    self.txn_resp["message"] = "Freezing energy in progress"
                    freeze_energy = self.energy - energy
                    await self.freeze(amount=50, resource="ENERGY")
                if bandwitch < self.bandwitch:
                    freeze_bandwitch = self.bandwitch - bandwitch
                    self.txn_resp["message"] = "Freezing bandwitch in progress"
                    print("На балансе недостаточно BANDWITCH, выполняется процесс пополнения BANDWITCH")
                    await self.freeze(amount=50, resource="BANDWIDTH")

            else:
                balance = await self.get_balance()
                if balance < float(self.trx_min_balance):
                    add_balance = float(self.trx_min_balance) - balance
                    print(f"Перевод {add_balance} TRX на кошелек <{self.transaction.address.address}>")
                    await self.activate_account(amount=add_balance)

        await self.transfer()

    async def activate_account(self, amount: float = 1):
        async with self.get_client() as client:
            txb = (
                client.trx.transfer(self._main_adds, self.transaction.address.address, int(amount * 1_000_000))
                .with_owner(self._main_adds)
                .fee_limit(self._fee_limit)
            )
            try:
                tx = await txb.build()
                p_key = PrivateKey(bytes.fromhex(self._main_pk_key))
                await tx.sign(p_key).broadcast()

            except Exception as e:
                self.txn_resp["status"] = "ERROR"
                self.txn_resp["message"] = "Activate account failed"
                print("MAIN ACCOUNT ERROR:", e)
            return self

    async def request_transaction_history_from_tron_api(self, address: Address):
        counter = 0
        _http_client = AsyncClient(timeout=Timeout(timeout=30, connect=5, read=5))
        ENDPOINT = "transaction"
        __url = f"{self.TRON_SCAN_API_URL}/{ENDPOINT}?sort=-timestamp&count=true&address={address.address}"
        response = await _http_client.get(__url)
        # _http_client.
        response_json = response.json()
        total = response_json["total"]
        transaction_list = response_json["data"]
        transaction_object_list = list()
        print(len(transaction_list))
        for tr in transaction_list:
            my_trans = Transaction()
            my_trans.tnx_id = tr["hash"]
            counter += 1
            print(counter)
