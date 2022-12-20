from Bot.utilts.settings import STAKE_MODE
from Dao.models.Address import Address
from Dao.models.Transaction import Transaction
from Services.CryptoMakers.Tron.Tron_Maker import Tron_Maker
from tronpy.keys import PrivateKey
from tronpy.exceptions import *


class Tron_TRC_Maker(Tron_Maker):

    async def get_balance(self,
                          contract: str,
                          address: Address):
        try:    #TODO Вероятное нарушение принципа LSP
            if await self.is_valid_address(address) is False:
                return float(0)
        except:
            pass
        async with self.get_client() as client:
            try:
                if contract:
                    contract = await client.get_contract(contract)
                    return float(await contract.functions.balanceOf(address) / 1_000_000)

                else:
                    return float(await client.get_account_balance(address))
            except AddressNotFound:
                return float(0)

    async def transfer(
            self,
            transaction: Transaction,
            fee_limit: float = None):

        txb = None
        address = transaction.address
        print("user_pk", address.private_key)
        p_key = PrivateKey(bytes.fromhex(address.private_key))

        async with self.get_client() as client:
            if transaction.network == "TRC-20" and transaction.token_contract_id:
                contract_f = await client.get_contract(transaction.token_contract_id)
                txb = await contract_f.functions.transfer(transaction.to_address, int(transaction.amount * 1_000_000))
                txb = txb.with_owner(transaction.from_address).fee_limit(self._fee_limit)
            elif transaction.network == "TRC-10":
                txb = (
                    client.trx.transfer(transaction.from_address, transaction.to_address,
                                        int(transaction.amount * 1_000_000))
                    .with_owner(transaction.from_address)
                    .fee_limit(self._fee_limit)
                )

            try:
                tx = await txb.build()
                txn_ret = await tx.sign(p_key).broadcast()
                self.txn_resp["status"] = "SUCCESS"
                self.txn_resp["message"] = "Transfer success"
                self.txn_resp["txn"] = await txn_ret.wait()
            except ValidationError:
                self.txn_resp["status"] = "ValidationError"
                self.txn_resp["message"] = "Account not active"
                self.txn_resp["txn"] = None
                await self.employer(transaction, fee_limit)
            except UnknownError:
                self.txn_resp["status"] = "BANDWITH_ERROR"
                self.txn_resp["message"] = "Energy or trx is not enough to transfer"
                self.txn_resp["txn"] = None
                await self.employer(transaction, fee_limit)
            return self

    async def employer(
            self,
            transaction: Transaction,
            fee_limit: float = None,
    ):
        txn_info = self.txn_resp
        if txn_info.get("status") == "ValidationError":
            self.txn_resp["status"] = "ActivateAccount"
            self.txn_resp["message"] = "account in the process of activation"
            print(f"Аккаунт не активирован, выполняeтся перевод 1 TRX на адрес {self._user_adds}")
            await self.activate_account(transaction)

        elif txn_info.get("status") == "BANDWITH_ERROR":
            self.txn_resp["status"] = "BandwitchError"
            if STAKE_MODE is True:
                account_resource = await self.account_resource(transaction)
                ENERGY = account_resource.get("ENERGY")
                BANDWITCH = account_resource.get("BANDWITCH")

                if ENERGY < self.energy:
                    print("На балансе недостаточно ENERGY, выполняется процесс пополнения ENERGY")
                    self.txn_resp["message"] = "Freezing energy in progress"
                    freeze_energy = self.energy - ENERGY
                    tn = await self.freeze(amount=50, receiver=transaction.from_address, resource="ENERGY")
                if BANDWITCH < self.bandwitch:
                    freeze_bandwitch = self.bandwitch - BANDWITCH
                    self.txn_resp["message"] = "Freezing bandwitch in progress"
                    print("На балансе недостаточно BANDWITCH, выполняется процесс пополнения BANDWITCH")
                    tn = await self.freeze(amount=50, receiver=transaction.from_address, resource="BANDWIDTH")
                else:
                    pass
            else:
                balance = await self.get_balance(address=transaction.from_address)
                print(balance)
                if float(balance) < float(self.trx_min_balance):
                    add_balance = float(self.trx_min_balance) - float(balance)
                    print(f"Перевод {add_balance} TRX на кошелек <{transaction.from_address}>")
                    await self.activate_account(transaction, add_balance)
        await self.transfer(transaction, fee_limit)
