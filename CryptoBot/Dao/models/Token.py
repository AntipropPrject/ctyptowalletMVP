from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from Dao.DB_Postgres.session import Base
from Dao.models.models import address_tokens


class Token(Base):
    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_Id = Column(String, nullable=True)
    token_name = Column(String)
    algorithm_name = Column(String, ForeignKey('algorithms.name', onupdate="CASCADE", ondelete="CASCADE"))
    network_id = Column(Integer, ForeignKey('networks.id', onupdate="CASCADE", ondelete="CASCADE"))

    addresses = relationship(
        "Address", secondary=address_tokens, back_populates="tokens", lazy="joined"
    )
    algorithm = relationship('Algorithm', lazy="joined", back_populates="tokens")
    network = relationship('Network', lazy="joined", back_populates="tokens")

    def __str__(self):
        return f"{self.token_name} [{self.network}]"

    def __eq__(self, other):
        if not isinstance(other, Token):
            return NotImplemented
        return self.token_name == other.token_name and self.network.name == other.network.name and self.contract_Id == other.contract_Id and self.algorithm_name == other.algorithm_name

    async def getBalance(self):
        pass
