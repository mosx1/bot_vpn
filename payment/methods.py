import json, enums, keyboards, enums.keyCall

from servers.methods import get_very_free_server

from yoomoneyMethods import getLinkPayment

from telebot.util import quick_markup

from tables import User

from users.methods import get_user_by_id

from payment.crypto.repository.methods import crypto_pay, PayingUser, TypeOfPurchase

from configparser import ConfigParser

from core.telebot import TeleBotMod
from telebot.types import Message

from sqlalchemy.orm import Session
from sqlalchemy import insert

from tables import SaleInvoicesInProgress

from connect import engine


def send_message_for_pay(bot: TeleBotMod, user_id: int, server_id: int, month: int, message: Message, label):

    conf = ConfigParser()
    conf.read('config.ini')
    
    # bot.send_message(
    #     conf['Telegram']['admin_chat'],
    #     f"Пользователь запросил ссылку на оплату\nid:{user_id}",
    #     disable_notification=True
    # )

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
        option_text = "Внимание! После оплаты необходимо будет заново настроить VPN по инструкции, которую отправит вам бот.\n\n"

    text_for_message = f"{option_text}Выберите способ оплаты (платежные ссылки действуют 1 час):"

    try:
        bot.edit_message_text_or_caption(
            message, 
            text_for_message,
            reply_markup=keyboard
        )
    except Exception:
        bot.send_message(
            message.chat.id,
            text_for_message,
            reply_markup=keyboard
        )


def add_sale_invoice(label: str, user_id: int, server_id: int, month_count: int, chat_id: int, message_id: int) -> None:
    with Session(engine) as session:
        query = insert(SaleInvoicesInProgress).values(
            telegram_id=user_id,
            label=label,
            server_id=server_id,
            month_count=month_count,
            chat_id=chat_id,
            message_id=message_id
        )
        session.execute(query)
        session.commit()    