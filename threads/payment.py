import time
import utils
import invite.methods

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
                    
                    invoice = invoice_item[0]
                    stop_date_time = invoice_item[1]
                    current_date_time = invoice_item[2]

                    info_last_payment: dict | None = getInfoLastPayment(invoice.label)

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
                                f'Не удалено сообщение\nпоток: check_payments\nerror: ```' + utils.form_text_markdownv2(str(e)) + "``` id:" + str(user.telegram_id),
                                parse_mode=ParseMode.mdv2.value
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
                                f'Не отправлено сообщение\nпоток: check_payments\nerror: ```' + utils.form_text_markdownv2(str(e)) + "``` id:" + str(user.telegram_id),
                                parse_mode=ParseMode.mdv2.value
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
                                f'Не изменено сообщение\nпоток: check_payments\nerror: ```' +utils.form_text_markdownv2(str(e)) + "``` id:" + str(user.telegram_id),
                                parse_mode=ParseMode.mdv2.value
                            )
                        
                    if (current_date_time > stop_date_time) or info_last_payment:
                        with Session(engine) as session:
                            query = delete(SaleInvoicesInProgress).where(SaleInvoicesInProgress.id == invoice.id)
                            session.execute(query)
                            session.commit()

                time.sleep(1)

        except Exception as e:
            print(str(e))