from sqlalchemy import Column, BigInteger, delete
from sqlalchemy.ext.asyncio import AsyncSession

from Dao.DB_Postgres.session import AlchemyMaster
from Dao.models.bot_models.bot_base import BotBase


class Admin(BotBase):
    __tablename__ = "admins"

    telegram_id = Column(BigInteger, primary_key=True)

    @AlchemyMaster.alchemy_session
    async def promote(self, alchemy_session: AsyncSession):
        alchemy_session.add(self)
        await alchemy_session.commit()

    @AlchemyMaster.alchemy_session
    async def demote(self, alchemy_session: AsyncSession):
        query = delete(Admin).where(Admin.telegram_id == self.telegram_id)
        await alchemy_session.execute(query)
        await alchemy_session.commit()

    @AlchemyMaster.alchemy_session
    async def check(self, alchemy_session: AsyncSession):
        is_legit = await alchemy_session.get(Admin, self.telegram_id)
        if is_legit:
            return True
        else:
            return False
