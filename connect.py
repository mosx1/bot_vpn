import telebot, logging, requests, time, threading, psycopg2
from configparser import ConfigParser

from sqlalchemy import Engine, create_engine

from config import FILE_URL


conf = ConfigParser()
conf.read(FILE_URL + 'config.ini')

token = conf['Telegram']['token_prod'] #general
token = conf['Telegram']['token_test']
bot = telebot.TeleBot(token)
logging.basicConfig(
    level=logging.INFO,
    filename = FILE_URL + "logs.txt",
    format="%(asctime)s %(levelname)s %(message)s"
)
postgres = conf['Postgres']

dbname: str = postgres.get('dbname')
user: str = postgres.get('user')
password: str = postgres.get('password')
host: str = postgres.get('host')


try:
    db = psycopg2.connect(
        dbname = conf['Postgres']['dbname'],
        user = conf['Postgres']['user'],
        password = conf['Postgres']['password'],
        host = conf['Postgres']['host']
    )
    db.autocommit = True
except Exception as e:
    logging.error("Подключиться к БД не удалось: " + str(e))

engine: Engine = create_engine('postgresql+psycopg2://', creator=lambda: db)

session = {}
len_offers_page = 4

def updateConnect():
    while True:
        requests.post(f"https://api.telegram.org/bot{token}/getUpdates")
        time.sleep(5)
        

update_tread = threading.Thread(target=updateConnect)
update_tread.start()
