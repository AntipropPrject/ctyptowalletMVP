import redis.asyncio as aioredis
from redis.asyncio.connection import ConnectionPool

from _config.variables import Data


class RedRedis:
    password = Data.redis_password
    host = Data.redis_host
    port = Data.redis_port
    cache_time = 86400
    bot_states_base = 0
    bot_storage_base = 1
    user_currency_cache_key = "Users:{user:n}:currency_set"
    data_redis: ConnectionPool

    @classmethod
    def states_base_url(cls):
        return f"redis://:{cls.password}@{cls.host}:{cls.port}/{cls.bot_states_base}"

    @classmethod
    async def connect_to_storage(cls):
        cls.data_redis = await aioredis.from_url(
            f"redis://:{cls.password}@{cls.host}:{cls.port}/{cls.bot_storage_base}", decode_responses=True)

    async def user_currency_cache_check(self, user_id: int, currency: str):
        return await self.data_redis.sismember(self.user_currency_cache_key.format(user=user_id), currency)

    async def user_currency_cache_update(self, user_id: int, currencies: set[str]):
        for currency in currencies:
            await self.data_redis.sadd(self.user_currency_cache_key.format(user=user_id), currency)
        await self.data_redis.expire(self.user_currency_cache_key.format(user=user_id), self.cache_time)


class DataRedis(RedRedis):
    auth_key = "authorized"
    text_key = "cached_texts"

    @classmethod
    async def set_data(cls, key: str, value: str | int, ttl: int = None):
        return await cls.data_redis.set(key, value, ex=ttl)

    @classmethod
    async def get_data(cls, key: str):
        data = await cls.data_redis.get(key)
        if data:
            return data

    @classmethod
    async def delete_data(cls, key: str):
        await cls.data_redis.delete(key)
        retry = await cls.get_data(key)
        if retry:
            raise Exception(f'Key {key} is not deleted!')

    @classmethod
    async def update_user_life(cls, user_id: int):
        alive_state = await cls.get_data(f"Users: {user_id}: {cls.auth_key}")
        new_value = alive_state if alive_state else "False"
        await cls.set_data(f"Users: {user_id}: {cls.auth_key}", new_value, ttl=6000)
        return alive_state

    @classmethod
    async def authorize(cls, telegram_user_id: int, uid: str):
        await cls.set_data(f"Users: {telegram_user_id}: {cls.auth_key}", uid, ttl=6000)


    @classmethod
    async def log_off(cls, telegram_user_id: int):
        await cls.delete_data(f"Users: {telegram_user_id}: {cls.auth_key}")


    @classmethod
    async def auth_cooldown(cls, telegram_user_id: int, add: bool = False):
        tries = await cls.get_data(f"Users: {telegram_user_id}: auth_tries")
        tries = int(tries) if tries else 0
        if add:
            tries += 1
            await cls.set_data(f"Users: {telegram_user_id}: auth_tries", tries, ttl=600)
        return tries

    @classmethod
    async def find_user(cls, telegram_user_id: int):
        return await cls.get_data(f"Users: {telegram_user_id}: {cls.auth_key}")

    @classmethod
    async def cache_text(cls, telegram_user_id: int, text: str, key: str):
        await cls.set_data(f"Users: {telegram_user_id}: {cls.text_key}: {key}", text, ttl=600)

    @classmethod
    async def get_cached_text(cls, telegram_user_id: int, key: str):
        return await cls.get_data(f"Users: {telegram_user_id}: {cls.text_key}: {key}")
