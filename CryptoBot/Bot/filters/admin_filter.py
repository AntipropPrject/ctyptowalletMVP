from aiogram.filters import Filter
from aiogram.types import CallbackQuery, Message

from Dao.DB_Postgres.session import AlchemyMaster
from Dao.models.bot_models.Admins import Admin
from _config.variables import Data


class IsAdmin(Filter):

    async def __call__(self, event: Message | CallbackQuery) -> bool:
        user_id = event.from_user.id

        if user_id in Data.superadmins:
            return True
        else:
            session_connect = await AlchemyMaster.create_session()
            async with session_connect() as session:
                if await session.get(Admin, user_id):
                    return True
        return False
