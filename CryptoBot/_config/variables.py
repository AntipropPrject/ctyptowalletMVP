import os

from aiogram import Bot


class Data:
    superadmins = set(map(int, os.getenv('SUPERADMINS').split(',')))
    redis_host = os.getenv('RED_HOST')
    redis_port = os.getenv('RED_PORT')
    redis_password = os.getenv('RED_PASS')
    main_bot_token = os.getenv('BOT_ID')
    postgres_host = os.getenv('POSTGRES_HOST')
    postgres_password = os.getenv('POSTGRES_PASSWORD')
    postgres_user = os.getenv('POSTGRES_USER')
    main_bot = Bot(main_bot_token, parse_mode="HTML")
    secret_key = os.getenv('SHA_KEY')
