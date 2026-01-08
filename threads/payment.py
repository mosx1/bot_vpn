import time
import utils
import invite

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

        config = ConfigParser()
        config.read('config.ini')
        
        with Session(engine) as session:
            query = select(
                SaleInvoicesInProgress, 
                (func.timezone('UTC', SaleInvoicesInProgress.create_date) - text("INTERVAL '1 hour'")).label("stop_date_time"),
                func.now().label("current_date_time")
            )
            result: Result = session.execute(query)
            invoices = result.fetchall()

        for invoice, stop_date_time, current_date_time in invoices:

            res = None
            t = ""
            res = getInfoLastPayment(invoice.label)

            if res:
                
                user: User = get_user_by_id(invoice.telegram_id)

                logging.info(
                    "user_id: {}; user_name:{}; Оплата подписки {} мес. сервер {}".format(
                        invoice.telegram_id,
                        user.name,
                        invoice.month_count,
                        utils.get_server_name_by_id(invoice.server_id)
                    )
                )

                bot.delete_message(
                    invoice.chat_id,
                    invoice.message_id
                )

                old_message: Message = bot.send_photo(
                    chat_id=user.telegram_id,
                    photo=open("4rrr.jpg", "rb"),
                    caption="Оплата получена, идет настройка конфигурации(это может занять несколько минут)..."
                )
        
                userMessage = add_user(
                    invoice.telegram_id,
                    invoice.month_count,
                    server=invoice.server_id
                )

                bot.send_message(
                    config['Telegram']['admin_chat'],
                    "[" + utils.form_text_markdownv2(user.name) + "](tg://user?id\=" + str(user.telegram_id) + ") оплатил",
                    parse_mode=ParseMode.mdv2.value
                )
                
                invite.methods.incrementBalance(
                    invoice.telegram_id, 
                    month=invoice.month_count
                )

                if not user.action:
                    t = "В связи с тем, что вы продлили подписку уже после ее отключения, Вам нужно заново настроить все\. Во избежании таких ситуаций в будущем \- продлевайте подписку после первого уведомления\.\n"
                    
                successfully_paid(
                    invoice.telegram_id,
                    old_message,
                    optionText=str(userMessage.value) + t
                )
            
            if (current_date_time > stop_date_time) or res:
                with Session(engine) as session:
                    query = delete(SaleInvoicesInProgress).where(SaleInvoicesInProgress.id == invoice.id)
                    session.execute(query)
                    session.commit()

        time.sleep(4)