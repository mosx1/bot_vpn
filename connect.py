import logging

from configparser import ConfigParser

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, async_sessionmaker

from core.aiogram import TeleBotMod


conf = ConfigParser()
conf.read('config.ini')

token = conf['Telegram']['token_test'] #general

bot = TeleBotMod(
    token
)

logging.basicConfig(
    level=logging.INFO,
    filename = "logs.txt",
    format="%(asctime)s %(levelname)s %(message)s"
)

engine: AsyncEngine = create_async_engine(
    f'postgresql+asyncpg://{conf['Postgres']['user']}:{conf['Postgres']['password']}@{conf['Postgres']['host']}/{conf['Postgres']['dbname']}'
)
AsyncSession = async_sessionmaker(engine)

session = {}
len_offers_page = 4