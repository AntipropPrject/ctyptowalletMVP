import asyncio

from Bot.bot import bot_start

if __name__ == '__main__':
    # asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(bot_start())
