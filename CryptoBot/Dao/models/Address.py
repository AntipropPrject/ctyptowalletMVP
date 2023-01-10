from sqlalchemy import Column, String, BigInteger, ForeignKey, Integer
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relationship
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy_utils import StringEncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesEngine

from Dao.DB_Postgres.session import Base
from Dao.models.Token import Token
from Dao.models.Transaction import Transaction
from Dao.models.models import address_tokens
from _config.variables import Data


class Address(Base):
    __tablename__ = "addresses"

    address = Column(String, primary_key=True)
    name = Column(StringEncryptedType(String, Data.secret_key, AesEngine), nullable=True)
    private_key = Column(StringEncryptedType(String, Data.secret_key, AesEngine))
    path_index = Column(Integer, default=0)

    wallet_id = Column(BigInteger, ForeignKey('wallets.id', onupdate="CASCADE", ondelete="CASCADE"))
    wallet = relationship("Wallet", lazy="joined", back_populates="addresses")
    transactions: dict[int, Transaction] = relationship(
        "Transaction",
        collection_class=attribute_mapped_collection("id"),
        cascade="all, delete-orphan", lazy="joined"
    )
    tokens = relationship(
        "Token", secondary=address_tokens, back_populates="addresses", lazy="joined"
    )

    token_list = association_proxy("tokens", "contract_Id", creator=lambda tokens: Token(contract_Id=tokens))

    def get_address_freezed_fee(self,
                                token_name: str) -> float:
        freezed_fee: float = 0
        for transaction in self.transactions.values():
            if transaction.token.token_name == token_name:
                if transaction.service_fee is not None:
                    freezed_fee = freezed_fee + transaction.service_fee
                else:
                    break
        return freezed_fee

    def __eq__(self, other):
        other: Address
        return self.address == other.address, self.private_key == other.private_key, self.path_index == other.path_index

    # Что это?
    def __count_transactions_in_db(self):
        transactions_in = dict(filter(lambda x: x.is_In(), self.transactions.values()))
        wallet = self.wallet
        owner = wallet.owner
        owner_datetime_come = owner.datetime_come
        print(transactions_in)
        return transactions_in  # , transactions_out

    # Что это?
    # async def __get_transactions_from_blockchain(self):
    #
    #
    #     return self.__count_transactions_in_db()
    async def public_fun(self):
        self.__count_transactions_in_db()
