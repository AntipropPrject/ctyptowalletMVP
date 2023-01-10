from sqlalchemy import Column, String, ForeignKey, Integer, Boolean
from sqlalchemy.orm import relationship

from Dao.DB_Postgres.session import Base


class Network(Base):
    __tablename__ = "networks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    mainnet = Column(Boolean)
    blockchain = Column(String, ForeignKey('blockchains.name', onupdate="CASCADE", ondelete="CASCADE"))

    tokens = relationship('Token', lazy="joined", back_populates="network")