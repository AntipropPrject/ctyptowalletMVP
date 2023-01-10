import inspect as pyth_inspect
import os

from sqlalchemy import MetaData, schema, inspect
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base(metadata=MetaData(schema="public"))


class AlchemyMaster:
    engine = None

    @classmethod
    def prepare_engine(cls, pg_username: str, pg_password: str, pg_host: str, pg_database: str = 'postgres'):
        cls.engine = create_async_engine(
            f"postgresql+asyncpg://{pg_username}:{pg_password}@{pg_host}/{pg_database}"
        )

    @classmethod
    async def create_tables(cls, declarative_bases: tuple[declarative_base, ...] | list[declarative_base, ...],
                            schemas: tuple[str, ...] | list[str, ...]):

        assert cls.engine, 'No engine is defined!'

        async with cls.engine.begin() as conn:
            all_schemas = await conn.run_sync(AlchemyMaster._check_shemas)
            for check_schema in schemas:
                if check_schema not in all_schemas:
                    await conn.execute(schema.CreateSchema(check_schema))

            for base in declarative_bases:
                await conn.run_sync(base.metadata.create_all)

    @staticmethod
    def _check_shemas(conn):
        inspector = inspect(conn)
        return inspector.get_schema_names()

    @classmethod
    async def create_session(cls):
        assert cls.engine, 'No engine is defined!'
        async_session = sessionmaker(cls.engine, expire_on_commit=False, class_=AsyncSession)
        return async_session

    @classmethod
    def alchemy_session(cls, function):
        async def wrap(*args, **kwargs):
            session_connect = await AlchemyMaster.create_session()
            async with session_connect() as session:
                kwargs['alchemy_session'] = session
                prepared_kwargs = {
                    k: v for k, v in kwargs.items()
                    if k in pyth_inspect.getfullargspec(function).args
                       or k in pyth_inspect.getfullargspec(function).kwonlyargs
                }
                return await function(*args, **prepared_kwargs)

        return wrap


async def create_session():
    engine = create_async_engine(
        f"postgresql+asyncpg://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}/postgres"
        # f"postgresql+asyncpg://postgres:PASSHERE@16.170.165.75:5454/postgres"
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
