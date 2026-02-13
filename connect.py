import logging

from telebot.storage import StateMemoryStorage

from configparser import ConfigParser

from core.telebot import TeleBotMod

from database import engine

conf = ConfigParser()
conf.read('config.ini')

token = conf['Telegram']['token_test']  # general

storage = StateMemoryStorage()

bot = TeleBotMod(
    token,
    state_storage=storage
)

logging.basicConfig(
    level=logging.INFO,
    filename="logs.txt",
    format="%(asctime)s %(levelname)s %(message)s"
)

session = {}
len_offers_page = 4
