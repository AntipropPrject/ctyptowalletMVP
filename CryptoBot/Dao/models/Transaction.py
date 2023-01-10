import datetime

from sqlalchemy import Column, BigInteger, Float, String, ForeignKey, DateTime, Integer
from sqlalchemy.orm import relationship

from Dao.DB_Postgres.session import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(BigInteger, primary_key=True, unique=True, autoincrement=True)
    tnx_id: str = Column(String)
    token_id = Column(Integer, ForeignKey('tokens.id', onupdate="CASCADE", ondelete="CASCADE"))
    amount = Column(Float)
    owner_address = Column(String, ForeignKey('addresses.address', onupdate="CASCADE", ondelete="CASCADE"))
    foreign_address = Column(String)
    datetime = Column(DateTime, default=datetime.datetime.now())
    status: str = Column(String)
    type: str = Column(String)
    service_fee: float = Column(Float)
    network_fee: float = Column(Float)
    foreign_related_UID: str = Column(String,
                                    ForeignKey('owners.id', onupdate="CASCADE", ondelete="CASCADE"), nullable=True)


    address = relationship("Address", lazy="joined", back_populates="transactions")
    token = relationship("Token", lazy="joined")

    def is_In(self) -> bool:
        return self.address.address != self.owner_address

    def __str__(self):
        return f"- Tnx link: {self.tnx_id}\n" \
               f"- {self.amount} from {self.owner_address} ==> {self.foreign_address}\n" \
               f"- Status: {self.status}\n\n"
