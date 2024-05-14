import requests, random, config, time, threading
from connect import logging, db, bot, form_text_markdownv2
from telebot import types
from managment_user import add_token

class WalletPay:
    def __init__(self, userID) -> None:
        self.userID = userID
        self.externalID = random.randrange(1000, 9999)

    def getPayLink(self):
        cur = db.cursor()
        headers = {
        'Wpay-Store-Api-Key': config.WALLET_API_KEY,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        }
        
        payload = {
        'amount': {
            'currencyCode': 'USD',  # выставляем счет в долларах США
            'amount': '1.00',
        },
        'description': 'Оплата 1 месяца подписки',
        'externalId': self.externalID,  # ID счета на оплату в вашем боте
        'timeoutSeconds': 60 * 60 * 24,  # время действия счета в секундах
        'customerTelegramUserId': self.userID,  # ID аккаунта Telegram покупателя
        'returnUrl': 'https://t.me/open_vpn_sale_bot',  # после успешной оплаты направить покупателя в наш бот
        'failReturnUrl': 'https://t.me/wallet',  # при отсутствии оплаты оставить покупателя в @wallet
        }

        response = requests.post(
        "https://pay.wallet.tg/wpay/store-api/v1/order",
        json=payload, headers=headers, timeout=10
        )
        data = response.json()

        if (response.status_code != 200) or (data['status'] not in ["SUCCESS", "ALREADY"]):
            logging.warning("# code: %s json: %s", response.status_code, data)
            return ''
        print(self.externalID, data)
        cur.execute("INSERT INTO orders (user, order_id) VALUES ((SELECT id FROM users_subscription WHERE t_id=" + str(self.userID) + "), " + str(data['data']['id']) + ")")
        db.commit()
        return data['data']['payLink']

def getOrderInfo():
    headers = {
        'Wpay-Store-Api-Key': config.WALLET_API_KEY,
    }
    cur = db.cursor()
    cur.execute("SELECT order_id FROM orders ORDER BY id DESC")
    data_cur = cur.fetchone()
    response = requests.get(
        "https://pay.wallet.tg/wpay/store-api/v1/order/preview?id=" + str(data_cur[0]),
        headers=headers,
        timeout=10
    )
    data = response.json()
    return data['data']['status'] #"ACTIVE" "EXPIRED" "PAID" "CANCELLED"

def getOrderList():
    while True:
        cur = db.cursor()
        headers = {
            'Wpay-Store-Api-Key': config.WALLET_API_KEY,
        }
        response = requests.get(
            "https://pay.wallet.tg/wpay/store-api/v1/reconciliation/order-list?offset=0&count=10",
            headers=headers,
            timeout=10
        )
        data = response.json()
        for i in data['data']['items']:
            cur.execute("SELECT user FROM orders WHERE order_id = " + str(i['id']))
            user_id = cur.fetchone()
            try:
                if len(cur.fetchone()) > 0:
                    if i['status'] == "PAID":
                        cur.execute("SELECT name, t_id FROM users_subscription WHERE id = " + str(user_id[0]))
                        dataCur = cur.fetchone()
                        name = dataCur[0]
                        t_id = dataCur[1]
                        key = types.InlineKeyboardMarkup()
                        key.add(*[types.InlineKeyboardButton(text=i, callback_data='{"key": "action", "id": "' + str(t_id) + '", "month": "' + str(i) + '"}') for i in range(1,13)], types.InlineKeyboardButton(text="Отклонить", callback_data='{"key": "not_action", "id": "' + str(t_id) + '"}'))
                        bot.send_message(config.ADMINCHAT, "Оплачен криптовалютой пользователем: [" + form_text_markdownv2(name) + "](tg://user?id\=" + str(t_id) + ")\. Подписка активирована автоматически\.", reply_markup=key, parse_mode="MarkdownV2")
                        add_token(t_id, month=1, name_user=name)
                        #cur.execute("DELETE FROM orders WHERE order_id = " + i['id']) включить после проверки работоспособности & продолжить обрабатывать события
                    elif (i['status'] == "EXPIRED") or (i['status'] == "CANCELLED"):
                        cur.execute("DELETE FROM orders WHERE order_id = " + i['id'])
            except Exception as e:
                logging.error("getPayLink : " + str(e))
        time.sleep(60)

updateOrderList = threading.Thread(target=getOrderList)
updateOrderList.start()