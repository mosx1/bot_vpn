import config, utils

from keyboards import KeyboardForUser

def onlyAdminChat():
    return lambda message: message.chat.id == config.ADMINCHAT


def only_user_chat():
    return lambda message: message.chat.id != config.ADMINCHAT


def only_user_chat_and_text():
    return lambda message: message.chat.id != config.ADMINCHAT and not message.text.startswith('/') and message.text != utils.get_list_values_from_enum(KeyboardForUser)