import telebot, logging, requests, time, threading, sqlite3
#token = '' #general
token = '' #test
bot = telebot.TeleBot(token)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
db = sqlite3.connect('db_vpn.db', check_same_thread=False)


session = {}
len_offers_page = 4

def updateConnect():
    while True:
        requests.post(f"https://api.telegram.org/bot/{token}/getUpdates".format(token))
        time.sleep(9)
        

update_tread = threading.Thread(target=updateConnect)
update_tread.start()



def form_text_markdownv2(message_text):
    temp = message_text
    try:
        for escaped_characters in ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']:
            if escaped_characters in message_text:
                message_text = str(message_text).replace(escaped_characters, "\\" + escaped_characters)
    except TypeError:
        logging.error("Переданное сообщение не является текстом")
        return temp
    return message_text
