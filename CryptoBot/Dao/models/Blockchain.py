from sqlalchemy import Column, String

from Dao.DB_Postgres.session import Base


class Blockchain(Base):
    __tablename__ = "blockchains"

    name = Column(String, primary_key=True)

