import config

from telebot.types import Message

def onlyAdminChat():
    return lambda message: message.chat.id == config.ADMINCHAT