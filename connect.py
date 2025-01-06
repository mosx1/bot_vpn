import telebot, logging, requests, time, threading, config, psycopg2
# token = config.TOKENPROD #general
token = config.TOKENTEST #test
bot = telebot.TeleBot(token)
logging.basicConfig(level=logging.INFO, filename="logs.txt", format="%(asctime)s %(levelname)s %(message)s")

try:
    db = psycopg2.connect(
        dbname='postgres',
        user='postgres',
        password='597730754',
        host='66.151.32.210'
    )
    db.autocommit = True
except Exception as e:
    logging.error("Подключиться к БД не удалось: " + str(e))



session = {}
len_offers_page = 4

def updateConnect():
    while True:
        requests.post(f"https://api.telegram.org/bot/{token}/getUpdates".format(token))
        time.sleep(5)
        

update_tread = threading.Thread(target=updateConnect)
update_tread.start()
