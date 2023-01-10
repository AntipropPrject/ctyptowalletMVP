from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from Dao.DB_Postgres.session import AlchemyMaster
from Dao.models.Address import Address
from Dao.models.Token import Token
from Dao.models.Transaction import Transaction
from Dao.models.Wallet import Wallet


class TransactionService:

    @staticmethod
    def __type_check(transaction_type: str):
        if transaction_type not in ['sending', 'receiving']:
            raise TypeError('Transaction type must be "sending" or "receiving"!')


    @staticmethod
    @AlchemyMaster.alchemy_session
    async def create_transaction(token: Token, owner_address: str, foreign_address: str, amount: float,
                                 fee: float, transaction_type: str,
                                 *,
                                 alchemy_session: AsyncSession):

        TransactionService.__type_check(transaction_type)

        owner_address_obj: Address = await alchemy_session.get(Address, owner_address)
        if not owner_address_obj:
            raise Exception(f'Cant find address {owner_address} in base!')

        foreign_address_obj: Address = await alchemy_session.get(Address, foreign_address)
        if foreign_address_obj:
            foreign_owner_uid = foreign_address_obj.wallet.owner_id
        else:
            foreign_owner_uid = None

        transaction = Transaction(token=token,
                                 amount=amount,
                                 foreign_address=foreign_address,
                                 address=owner_address_obj,
                                 service_fee=fee,
                                 type=transaction_type,
                                 foreign_related_UID=foreign_owner_uid
        )
        return transaction


    @staticmethod
    @AlchemyMaster.alchemy_session
    async def get_user_transactions(u_id: str, transaction_type: str | None = None, address: str | None = None,
                                    *, alchemy_session: AsyncSession):
        if transaction_type:
            TransactionService.__type_check(transaction_type)

        if transaction_type:
            query = select(Transaction).filter(Transaction.type == transaction_type,
                                           Transaction.address.has(
                                               Address.wallet.has(Wallet.owner_id == u_id))
                                               ).order_by(Transaction.datetime.asc())
        else:
            query = select(Transaction).filter(
                Transaction.address.has(Address.wallet.has(Wallet.owner_id == u_id))
            ).order_by(
                Transaction.datetime.asc())

        if address:
            query = query.filter(Transaction.address.has(Address.address == address))

        raw_result = (await alchemy_session.execute(query)).unique()
        transaction_list = [transaction for raw in raw_result for transaction in raw]
        return transaction_list
