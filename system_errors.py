from configparser import ConfigParser
from core.telebot import TeleBotMod

class ErrorInMessage:
    def __init__(self, bot: TeleBotMod, exception_text: str) -> None:
        
        config = ConfigParser()
        config.read('config.ini')

        bot.send_message(config['Telegram']['admin_chat'], exception_text)