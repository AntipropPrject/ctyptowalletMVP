from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship

from Dao.DB_Postgres.session import Base


class Algorithm(Base):
    __tablename__ = "algorithms"

    name = Column(String, primary_key=True)
    blockchain = Column(String, ForeignKey('blockchains.name', onupdate="CASCADE", ondelete="CASCADE"))
    tokens = relationship('Token', lazy="joined", back_populates="algorithm")
