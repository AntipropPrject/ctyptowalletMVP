from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from Dao.DB_Postgres.session import Base
from Dao.models.models import address_tokens


class Token(Base):
    __tablename__ = "tokens"

    contract_Id = Column(String, primary_key=True)
    token_name = Column(String)
    network = Column(String)

    addresses = relationship(
        "Address", secondary=address_tokens, back_populates="tokens", lazy="joined"
    )
    def __str__(self):
        return f"{self.token_name} [{self.network}]"

    def __eq__(self, other):
        if not isinstance(other, Token):
            return NotImplemented

        return self.token_name == other.token_name and self.network == other.network and self.contract_Id == other.contract_Id

    async def getBalance(self):
        pass
