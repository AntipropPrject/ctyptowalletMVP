from aiogram import Dispatcher
from aiogram.client.session import aiohttp
from aiogram.fsm.storage.redis import RedisStorage

from AllLogs.bot_logger import main_logger
from Bot.handlers import start_hand
from Bot.handlers.admin_handlers import main_admin_hand
from Bot.handlers.main_handlers import auth_hand, main_menu_hand, registration_hand
from Bot.handlers.main_handlers.wallet_handlers import main_wallet_hand
from Bot.handlers.service_handlers import return_hand, AML_check_hand
from Bot.middleware.alchemy_session_middle import DbSession
from Bot.middleware.alive_middle import AliveMiddleware
from Dao.DB_Postgres.session import AlchemyMaster, Base
from Dao.DB_Redis import RedRedis
from Dao.models.bot_models.bot_base import BotBase
from Services.StaticInfoService import StaticInfoService
from _config.variables import Data

storage = RedisStorage.from_url(RedRedis.states_base_url())
dp = Dispatcher(storage=storage)


async def bot_start():
    main_logger.infolog.info('Logger is ready!')

    bot = Data.main_bot
    bot_info = await bot.get_me()

    print(f"Bot was reborn as\n"
          f"|- {bot_info.full_name} -|- @{bot_info.username} -|\n"
          f"What a time to be alive!\n")

    AlchemyMaster.prepare_engine(pg_username=Data.postgres_user,
                                 pg_password=Data.postgres_password,
                                 pg_host=Data.postgres_host)
    await AlchemyMaster.create_tables(declarative_bases=(Base, BotBase),
                                      schemas=('public', 'bot'))
    session_db = await AlchemyMaster.create_session()

    dp.message.middleware(DbSession(session_db))
    dp.callback_query.middleware(DbSession(session_db))
    dp.message.middleware(AliveMiddleware())

    dp.include_router(start_hand.router)
    dp.include_router(main_admin_hand.router)
    dp.include_router(registration_hand.router)
    dp.include_router(auth_hand.router)

    dp.include_router(main_menu_hand.router)
    dp.include_router(return_hand.router)

    dp.include_router(main_wallet_hand.router)
    # dp.include_router(transfer_hand.router)

    dp.include_router(AML_check_hand.router)

    await StaticInfoService.fill_bases()

    session = aiohttp.ClientSession()
    await session.close()

    await RedRedis.connect_to_storage()
    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
