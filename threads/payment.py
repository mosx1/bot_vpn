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

from servers.methods import get_url_mtproto


def check_payments() -> None:

    config = ConfigParser()
    config.read('config.ini')

    while True:
        
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
                
                if not invoice.is_gift and info_last_payment and invoice.server_id:
                    success_payment(invoice, config)
                # if invoice.is_gift and (invoice.telegram_id == config['Telegram'].getint('admin_chat') or (info_last_payment and not invoice.server_id)):
                #     success_payment_gift(invoice, config)

                if (
                    current_date_time.strftime("%Y-%m-%d %H:%M:%S") > stop_date_time.strftime("%Y-%m-%d %H:%M:%S")
                    ) or info_last_payment or (
                        invoice.telegram_id == config['Telegram'].getint('admin_chat') and invoice.is_gift
                    ):
                    del_invoice(invoice)

        time.sleep(3)


def success_payment(invoice: SaleInvoicesInProgress, config: ConfigParser):
    """
    Process successful payment with proper error handling and transaction safety.
    Only deletes invoice if payment processing completes successfully.
    """
    user: User | None = get_user_by_id(invoice.telegram_id)

    if not user:
        logging.error(f'User not found for invoice {invoice.id}, telegram_id: {invoice.telegram_id}')
        return

    logging.info(
        "user_id: {}; user_name:{}; Оплата подписки {} мес. сервер {}".format(
            user.telegram_id,
            user.name,
            invoice.month_count,
            utils.get_server_name_by_id(invoice.server_id)
        )
    )

    # Step 1: Delete old payment message (non-critical)
    if invoice.message_id:
        try:
            bot.delete_message(
                user.telegram_id,
                invoice.message_id
            )
        except Exception as e:
            logging.error(f'Failed to delete payment message for user {user.telegram_id}: {str(e)}')
            bot.send_message(
                config['Telegram']['admin_chat'],
                f'Не удалено сообщение\nпоток: check_payments\nerror: ```' + utils.form_text_markdownv2(str(e)) + "``` id:" + str(user.telegram_id)
            )

    # Step 2: Send "processing" message with proper file handle management
    old_message: Message | None = None
    try:
        with open("static/logo_big.jpeg", "rb") as photo:
            old_message = bot.send_photo(
                user.telegram_id,
                photo=photo,
                caption="Оплата получена, идет настройка конфигурации(это может занять несколько минут)..."
            )
    except Exception as e:
        logging.error(f'Failed to send processing message for user {user.telegram_id}: {str(e)}')
        bot.send_message(
            config['Telegram']['admin_chat'],
            f'Не отправлено сообщение\nпоток: check_payments\nerror: ```' + utils.form_text_markdownv2(str(e)) + "``` id:" + str(user.telegram_id)
        )

    # Step 3: Add/extend user subscription (critical operation)
    try:
        userMessage = add_user(
            user.telegram_id,
            invoice.month_count,
            server=invoice.server_id
        )
    except Exception as e:
        logging.error(f'Failed to add user subscription for {user.telegram_id}: {str(e)}')
        bot.send_message(
            config['Telegram']['admin_chat'],
            f'Ошибка при активации подписки\nпоток: check_payments\nerror: ```' + utils.form_text_markdownv2(str(e)) + "``` id:" + str(user.telegram_id)
        )
        # Don't delete invoice - allow retry
        return

    # Step 4: Notify admin
    try:
        bot.send_message(
            config['Telegram']['admin_chat'],
            "[" + utils.form_text_markdownv2(user.name) + "](tg://user?id\=" + str(user.telegram_id) + ") оплатил",
            parse_mode=ParseMode.mdv2.value
        )
    except Exception as e:
        logging.error(f'Failed to notify admin about payment from {user.telegram_id}: {str(e)}')

    # Step 5: Increment referral balance (non-critical)
    try:
        invite.methods.incrementBalance(
            user.telegram_id,
            month=invoice.month_count
        )
    except Exception as e:
        logging.error(f'Failed to increment balance for {user.telegram_id}: {str(e)}')

    # Step 6: Send success message (only delete invoice if this succeeds)
    try:
        successfully_paid(
            user.telegram_id,
            old_message,
            optionText=str(userMessage.value)
        )
        # Only delete invoice after successful completion
        del_invoice(invoice)
    except Exception as e:
        logging.error(f'Failed to send success message for {user.telegram_id}: {str(e)}')
        bot.send_message(
            config['Telegram']['admin_chat'],
            f'КРИТИЧЕСКАЯ ОШИБКА ОБНОВЛЕНИЯ ПОСЛЕ ОПЛАТЫ Не изменено сообщение\nпоток: check_payments\nerror: ```' + utils.form_text_markdownv2(str(e)) + "``` id:" + str(user.telegram_id)
        )
        # Don't delete invoice - will retry on next cycle


def success_payment_gift(invoice: SaleInvoicesInProgress, config: ConfigParser):
    """
    Process successful gift payment with proper error handling and file handle management.
    """
    user: User | None = get_user_by_id(invoice.telegram_id)

    if not user:
        logging.error(f'User not found for gift invoice {invoice.id}, telegram_id: {invoice.telegram_id}')
        return

    logging.info(
        "user_id: {}; user_name:{}; Оплата подарочной подписки {} мес.".format(
            user.telegram_id,
            user.name,
            invoice.month_count
        )
    )

    # Step 1: Generate gift code
    try:
        hash = genGiftCode(invoice.month_count)
    except Exception as e:
        logging.error(f'Failed to generate gift code for invoice {invoice.id}: {str(e)}')
        bot.send_message(
            config['Telegram']['admin_chat'],
            f'Ошибка генерации подарочного кода\nпоток: check_payments\nerror: ```' + utils.form_text_markdownv2(str(e)) + "```"
        )
        return

    # Step 2: Notify admin about gift purchase
    try:
        bot.send_message(
            config['Telegram'].getint('admin_chat'),
            "[{}](tg://user?id\={}) оплатил подарочную подписку".format(utils.form_text_markdownv2(user.name), user.telegram_id),
            parse_mode=ParseMode.mdv2.value
        )
    except Exception as e:
        logging.error(f'Failed to notify admin about gift purchase by {user.telegram_id}: {str(e)}')

    # Step 3: Delete payment message
    try:
        bot.delete_message(
            invoice.chat_id,
            invoice.message_id
        )
    except Exception as e:
        logging.error(f'Failed to delete gift payment message: {str(e)}')

    # Step 4: Get MTProto URL
    try:
        mtproto = get_url_mtproto(user.server_id)
    except Exception as e:
        logging.error(f'Failed to get MTProto URL for server {user.server_id}: {str(e)}')
        mtproto = "Недоступно"

    # Step 5: Send gift photo with proper file handle management
    photoMessage: Message | None = None

    with open("static/logo_big.jpeg", "rb") as photo:
        photoMessage = bot.send_photo(
            chat_id=user.telegram_id,
            photo=photo,
            caption=config['MessagesTextMD'].get('gift_postcard').format(
                code=hash,
                date=invoice.month_count,
                mtproto=mtproto
            ),
            parse_mode=ParseMode.mdv2.value
        )

    # Step 6: Send reply message
    try:
        bot.reply_to(
            photoMessage,
            "Перешлите это сообщение другу в качестве подарка. Спасибо что помогаете нам делать интернет доступнее."
        )
    except Exception as e:
        logging.error(f'Failed to send reply to gift message for {user.telegram_id}: {str(e)}')

    # Step 7: Final admin notification
    try:
        bot.send_message(
            config['Telegram']['admin_chat'],
            "[" + utils.form_text_markdownv2(user.name) + "](tg://user?id\=" + str(user.telegram_id) + ") оплатил подарочную подписку",
            parse_mode=ParseMode.mdv2.value
        )
    except Exception as e:
        logging.error(f'Failed to send final admin notification for gift by {user.telegram_id}: {str(e)}')

    # Step 8: Delete invoice after successful completion
    del_invoice(invoice)


def del_invoice(invoice: SaleInvoicesInProgress):
    with Session(engine) as session:
        query = delete(SaleInvoicesInProgress).where(SaleInvoicesInProgress.id == invoice.id)
        session.execute(query)
        session.commit()