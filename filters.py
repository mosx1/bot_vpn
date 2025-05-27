import config

def onlyAdminChat():
    return lambda message: message.chat.id == config.ADMINCHAT

def only_user_chat():
    return lambda message: message.chat.id != config.ADMINCHAT