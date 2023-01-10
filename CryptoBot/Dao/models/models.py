from sqlalchemy import Column, ForeignKey, Table

from Dao.DB_Postgres.session import Base

# Base_api = 'https://rest.cryptoapis.io'
# API_version = "/v2"
# Base_api = Base_api + API_version

address_tokens = Table(
    "address_tokens",
    Base.metadata,
    Column("address_id", ForeignKey("addresses.address", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True),
    Column("token_id", ForeignKey("tokens.id", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True),
)


