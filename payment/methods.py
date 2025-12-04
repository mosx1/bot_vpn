import json, config, pytz, datetime, enums, keyboards, enums.keyCall

from servers.methods import get_very_free_server

from yoomoneyMethods import getLinkPayment

from telebot.util import quick_markup

from tables import User

from users.methods import get_user_by_id

from payment.crypto.repository.methods import crypto_pay, PayingUser, TypeOfPurchase

from configparser import ConfigParser

from core.telebot import TeleBotMod
from telebot.types import Message


def send_message_for_pay(bot: TeleBotMod, user_id: int, server_id: int, month: int, message: Message):

    conf = ConfigParser()
    conf.read(config.FILE_URL + 'config.ini')
    
    user: User = get_user_by_id(user_id)
    
    if user.action:
        server_id = user.server_id
    else:
        server_id = get_very_free_server()

    data = crypto_pay.create_invoice(month)
    crypto_pay.ids[data['invoice_id']] = PayingUser(
        user_id,
        month,
        server_id,
        message.id,
        TypeOfPurchase.yourself
    )


    label = (str(user_id) + 
            str(datetime.datetime.now(pytz.timezone('Europe/Moscow')))).replace(" ", "").replace("-","").replace("+", "").replace(".", "").replace(":", "")

    link_payment: str = getLinkPayment(label, month)

    keyboard: keyboards.InlineKeyboardMarkup = quick_markup(
        {
            'Оплата рублями': {'url': link_payment},
            "Оплата Crypto Bot": {"url": data['mini_app_invoice_url']},
            "Оплата звездами": {
                "callback_data": json.dumps(
                    {
                        "key": enums.keyCall.KeyCall.payment_stars.name, 
                        "amount": conf['Price'].getint('star') * int(month), 
                        "server": server_id
                    }
                )
            },
            '<<< назад': {'callback_data': '{"key": "pollCountMonth", "server": ' + str(server_id) + '}'}
        },
        row_width=1
    )
    

    option_text = ""
    if int(user.server_id) != int(server_id):
        option_text = "\n\nВнимание! После оплаты необходимо будет заново настроить VPN по инструкции, которую отправит вам бот."

    try:
        bot.edit_message_text_or_caption(
            message, 
            "Выберите способ оплаты:",
            reply_markup=keyboard
        )
    except Exception:
        bot.send_message(
            message.chat.id,
            "Выберите способ оплаты",
            reply_markup=keyboard
        )