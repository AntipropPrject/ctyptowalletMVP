from sqlalchemy.engine import CursorResult

from Dao.DB_Postgres.session import AlchemyMaster


async def getPkey_by_address_id(address_id:str)-> str:
    query = f""" SELECT private_key FROM addresses WHERE addresses.address = '{address_id}'"""
    session = await AlchemyMaster.create_session()
    async with session() as session:
        result: CursorResult = await session.execute(query)
        return result.first()[0]

