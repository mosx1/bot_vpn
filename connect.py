import telebot, logging, requests, time, threading, sqlite3
#token = '6353725892:AAEO8alOy5WfKH1K59ksH4SQYir3kQqp5g8' #general
token = '5262948613:AAGAL9LLKr4HvuOTwJkB1Kp58vbQrVYZqF8' #test
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



def ct():
    cur = db.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users_subscription
        (
            id integer NOT NULL,
            t_id integer NOT NULL,
            name character varying(50),
            datetime character varying(50),
            action integer NOT NULL,
            password character varying(50),
            paid integer,
            id_server integer,
            link_server character varying(255),
            server text,
            PRIMARY KEY (id)
        );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS referal
        (
            id integer NOT NULL,
            t_id_who integer NOT NULL,
            t_id_whom integer NOT NULL,
            PRIMARY KEY (id)
        );
    """)
    db.commit()
    logging.info("таблица создана")

#ct()

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
