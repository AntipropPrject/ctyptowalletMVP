import itertools
from typing import Any

from sqlalchemy import String, Column, select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from AllLogs.bot_logger import main_logger
from Dao.DB_Postgres.session import AlchemyMaster
from Dao.models.bot_models.bot_base import BotBase


class ContentUnit(BotBase):
    __tablename__ = "content"

    tag = Column(String, primary_key=True)
    text = Column(String)
    media_id = Column(String)
    media_type = Column(String)

    _formatting_vars = dict()

    @AlchemyMaster.alchemy_session
    async def add(self, alchemy_session: AsyncSession):
        search = await self.get()
        if search:
            unit: ContentUnit = search
            unit.text = self.text
            unit.media_id = self.media_id
            unit.media_type = self.media_type
        else:
            unit = self
        alchemy_session.add(unit)
        await alchemy_session.commit()

    @AlchemyMaster.alchemy_session
    async def get(self, alchemy_session: AsyncSession):
        assert self.tag, "You need to have tag in ContentUnit to get it!"
        unit: ContentUnit = await alchemy_session.get(ContentUnit, self.tag)
        if not unit:
            main_logger.infolog.info(f"There is no content unit at tag {self.tag}, returning empty string.")
            unit = ContentUnit(tag=self.tag, text=str())
        unit.__dict__['formatting_vars'] = dict()
        return unit

    @AlchemyMaster.alchemy_session
    async def delete(self, alchemy_session: AsyncSession):
        query = delete(ContentUnit).where(ContentUnit.tag == self.tag)
        await alchemy_session.execute(query)
        await alchemy_session.commit()

    @staticmethod
    @AlchemyMaster.alchemy_session
    async def get_all_tags(alchemy_session: AsyncSession) -> tuple | None:
        query = select(ContentUnit.tag)
        tags = (await alchemy_session.execute(query)).all()
        tags_unpacked = tuple(itertools.chain(*tags))
        return tags_unpacked

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.formatting_vars = dict()

    def add_formatting_vars(self, **kwargs):
        self.__dict__['_formatting_vars'] = kwargs

    def formatted_text(self):
        txt = self.text
        for var in self._formatting_vars:
            try:
                txt = txt.replace(f"{ '{' + var + '}' }", str(self._formatting_vars[var]))
            except Exception as err:
                main_logger.infolog.warn(f'Unknown error {err} in {self.tag} text')
        return txt
