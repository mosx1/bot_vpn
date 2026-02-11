import time
import utils
import invite.methods
import pytz

from connect import bot, logging, engine

from telebot.types import Message

from tables import User, SaleInvoicesInProgress

from users.methods import get_user_by_id

from yoomoneyMethods import getInfoLastPayment

from enums.parse_mode import ParseMode

from messageForUser import successfully_paid

from managment_user import add_user

from configparser import ConfigParser

from sqlalchemy.orm import Session
from sqlalchemy import select, delete, text, func
from sqlalchemy.engine import Result

from datetime import datetime, timedelta

from giftUsers import genGiftCode


def check_payments() -> None:

    while True:
        try:
            config = ConfigParser()
            config.read('config.ini')
            
            with Session(engine) as session:
                query = select(
                    SaleInvoicesInProgress, 
                    (SaleInvoicesInProgress.create_date + text("INTERVAL '1 hour'")).label("stop_date_time"),
                    func.now().label("current_date_time")
                )
                result: Result = session.execute(query)
                invoices = result.fetchall()
                
                for invoice_item in invoices:
                    
                    invoice: SaleInvoicesInProgress = invoice_item[0]
                    stop_date_time = invoice_item[1]
                    current_date_time = invoice_item[2]

                    try:
                        info_last_payment: dict | None = getInfoLastPayment(invoice.label)
                    except Exception as e:
                        print(str(e))
                        continue
                    
                    if info_last_payment:

                        user: User = get_user_by_id(invoice.telegram_id)
                        
                        logging.info(
                            "user_id: {}; user_name:{}; Оплата подписки {} мес. сервер {}".format(
                                user.telegram_id,
                                user.name,
                                invoice.month_count,
                                utils.get_server_name_by_id(invoice.server_id)
                            )
                        )

                        try:
                            bot.delete_message(
                                user.telegram_id,
                                invoice.message_id
                            )
                        except Exception as e:
                            bot.send_message(
                                config['Telegram']['admin_chat'],
                                f'Не удалено сообщение\nпоток: check_payments\nerror: ```' + utils.form_text_markdownv2(str(e)) + "``` id:" + str(user.telegram_id)
                            )

                        try:
                            old_message: Message = bot.send_photo(
                                user.telegram_id,
                                photo=open("4rrr.jpg", "rb"),
                                caption="Оплата получена, идет настройка конфигурации(это может занять несколько минут)..."
                            )
                        except Exception as e:
                            bot.send_message(
                                config['Telegram']['admin_chat'],
                                f'Не отправлено сообщение\nпоток: check_payments\nerror: ```' + utils.form_text_markdownv2(str(e)) + "``` id:" + str(user.telegram_id)
                            )

                        userMessage = add_user(
                            user.telegram_id,
                            invoice.month_count,
                            server=invoice.server_id
                        )

                        bot.send_message(
                            config['Telegram']['admin_chat'],
                            "[" + utils.form_text_markdownv2(user.name) + "](tg://user?id\=" + str(user.telegram_id) + ") оплатил",
                            parse_mode=ParseMode.mdv2.value
                        )

                        invite.methods.incrementBalance(
                            user.telegram_id, 
                            month=invoice.month_count
                        )

                        try:
                            successfully_paid(
                                user.telegram_id,
                                old_message,
                                optionText=str(userMessage.value)
                            )
                        except Exception as e:
                            bot.send_message(
                                config['Telegram']['admin_chat'],
                                f'Не изменено сообщение\nпоток: check_payments\nerror: ```' + utils.form_text_markdownv2(str(e)) + "``` id:" + str(user.telegram_id)
                            )

                    if (current_date_time.strftime("%Y-%m-%d %H:%M:%S") > stop_date_time.strftime("%Y-%m-%d %H:%M:%S")) or info_last_payment:
                        with Session(engine) as session:
                            query = delete(SaleInvoicesInProgress).where(SaleInvoicesInProgress.id == invoice.id)
                            session.execute(query)
                            session.commit()

                time.sleep(2)

        except Exception as e:
            print(str(e))


def polling_info_last_payment_gift(*args) -> dict:
    """
        args - label, month, userId, message
    """
    label = args[0]
    month = args[1]
    userId = int(args[2])
    message: Message = args[3]
    try:
        userName = args[5]
    except Exception:
        userName = userId

    stopDateTime = datetime.now(pytz.timezone('Europe/Moscow')) + timedelta(hours=1)

    while True:

        time.sleep(3)
        currentDateTime = datetime.now(pytz.timezone('Europe/Moscow'))
        res = getInfoLastPayment(label)

        config = ConfigParser()
        config.read('config.ini')

        if res or userId == config['Telegram'].getint('admin_chat'):

            logging.info(
                "user_id: {}; user_name:{}; Оплата подарочной подписки {} мес.".format(
                    userId,
                    userName,
                    month
                )
            )

            hash = genGiftCode(month)

            bot.send_message(
                config['Telegram'].getint('admin_chat'),
                "[{}](tg://user?id\={}) оплатил подарочную подписку".format(utils.form_text_markdownv2(userName), userId),
                parse_mode=ParseMode.mdv2.value
            )
            bot.delete_message(
                message.chat.id, 
                message.id
            )

            photoMessage: Message = bot.send_photo(
                chat_id=userId,
                photo=open("image/gift.png", "rb"),
                caption=config['MessagesTextMD'].get('gift_postcard').format(code=hash, date=month),
                parse_mode=ParseMode.mdv2.value
            )

            bot.reply_to(photoMessage, "Перешлите это сообщение другу в качестве подарка. Спасибо что помогаете нам делать интернет доступнее.")

            return res
        
        if currentDateTime > stopDateTime:
            return 