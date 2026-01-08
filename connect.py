import logging, psycopg2

from telebot.storage import StateMemoryStorage

from configparser import ConfigParser

from sqlalchemy import Engine, create_engine

from core.telebot import TeleBotMod


conf = ConfigParser()
conf.read('config.ini')

token = conf['Telegram']['token_prod'] #general

storage = StateMemoryStorage()

bot = TeleBotMod(
    token,
    state_storage=storage
)

logging.basicConfig(
    level=logging.INFO,
    filename = "logs.txt",
    format="%(asctime)s %(levelname)s %(message)s"
)
postgres = conf['Postgres']

dbname: str = postgres.get('dbname')
user: str = postgres.get('user')
password: str = postgres.get('password')
host: str = postgres.get('host')


db = psycopg2.connect(
    dbname = conf['Postgres']['dbname'],
    user = conf['Postgres']['user'],
    password = conf['Postgres']['password'],
    host = conf['Postgres']['host']
)
db.autocommit = True


engine: Engine = create_engine('postgresql+psycopg2://', creator=lambda: db)

session = {}
len_offers_page = 4