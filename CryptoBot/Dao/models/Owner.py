import datetime

from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy_utils import StringEncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesEngine

from Dao.DB_Postgres.session import Base
from Dao.models.Wallet import Wallet
from _config.variables import Data


class Owner(Base):
    __tablename__ = "owners"

    id = Column(StringEncryptedType(String, Data.secret_key, AesEngine), primary_key=True, unique=True)
    datetime_come = Column(DateTime, default=datetime.datetime.now())
    password = Column(StringEncryptedType(String, Data.secret_key, AesEngine), default=None)
    wallets: dict[str, Wallet] = relationship(
        "Wallet",
        collection_class=attribute_mapped_collection("blockchain"),
        cascade="all, delete-orphan", lazy="joined"
    )
