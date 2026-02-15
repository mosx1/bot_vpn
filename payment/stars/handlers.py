import utils, config, invite

from telebot import TeleBot
from telebot.types import LabeledPrice, Message

from connect import bot

from managment_user import add_user

from enums.parse_mode import ParseMode
from enums.logs import TypeLogs

from messageForUser import successfully_paid

from users.methods import get_user_by_id

from tables import User

from configparser import ConfigParser


def register_message_handlers(bot: TeleBot) -> None:

    # Обработчик предварительного подтверждения платежа
    @bot.pre_checkout_query_handler(func=lambda query: True)
    def process_pre_checkout(pre_checkout_query) -> None:
        # Проверяем данные (можно добавить логику проверки)
        bot.answer_pre_checkout_query(
            pre_checkout_query.id,
            ok=True,  # Разрешаем платеж (или False, если что-то не так)
            error_message="Ошибка оплаты"  # Сообщение об ошибке (если ok=False)
        )

    # Обработчик успешного платежа
    @bot.message_handler(content_types=['successful_payment'])
    def handle_successful_payment(message: Message) -> None:
        
        conf = ConfigParser()
        conf.read('config.ini')
        price_stars: int = conf['Price'].getint('star')
        summ: int = message.successful_payment.total_amount
        month = int(summ / price_stars)
        server = int(message.successful_payment.invoice_payload.split('server:')[-1])
        user: User = get_user_by_id(message.from_user.id)
        server_name: str = utils.get_server_name_by_id(server)

        utils.write_log(
            TypeLogs.info, 
            user, 
            f'Оплата подписки {month} мес. сервер {server_name}'
        )

        old_message: Message = bot.send_message(
            user.telegram_id,
            "Оплата получена, идет настройка конфигурации(это может занять несколько минут)..."
        )
        
        userMessage: config.AddUserMessage = add_user(user.telegram_id, month, server=server)

        bot.send_message(
            config.ADMINCHAT,
            "[" + utils.form_text_markdownv2(user.name) + "](tg://user?id\=" + str(user.telegram_id) + ") оплатил звездами",
            parse_mode=ParseMode.mdv2.value
        )
        bot.delete_message(
            old_message.chat.id, 
            old_message.id
        )
        
        invite.methods.incrementBalance(user.telegram_id, summ=summ)
        
        successfully_paid(user.telegram_id, optionText=userMessage.value)
        # bot.send_message(
        #     message.chat.id,
        #     "✅ **Оплата прошла успешно!** Спасибо за покупку!\n"
        #     f"ID платежа: `{message.successful_payment.telegram_payment_charge_id}`"
        # )
        if conf['Telegram'].getint('admin_chat') == message.from_user.id:
            handle_successful_payment_revorke(message)


    @bot.message_handler(commands=['revorke'])
    def handle_successful_payment_revorke(message: Message) -> None:
        """
            Возврат звезд
        """
        if bot.refund_star_payment(
            message.from_user.id,
            message.successful_payment.telegram_payment_charge_id
        ):
            bot.send_message(message.chat.id, "✅ Возврат успешно выполнен!")
        else:
            bot.send_message(message.chat.id, f"❌ Ошибка!")


def handler_get_pay(
        user_id,
        month,
        server,
        message_id
):
    user: User = get_user_by_id(user_id)
    server_name: str = utils.get_server_name_by_id(server)

    utils.write_log(
        TypeLogs.info, 
        user, 
        f'Оплата подписки {month} мес. сервер {server_name}'
    )

    bot.edit_message_caption("Оплата получена, идет настройка конфигурации(это может занять несколько минут)...", user_id, message_id)
    
    userMessage: config.AddUserMessage = add_user(user_id, month, server=server)

    bot.send_message(
        config.ADMINCHAT,
        "[" + utils.form_text_markdownv2(user.name) + "](tg://user?id\=" + str(user_id) + ") оплатил",
        parse_mode=ParseMode.mdv2.value
    )
    bot.delete_message(user_id, message_id)
    
    invite.methods.incrementBalance(user_id, month=month)
    
    successfully_paid(user_id, optionText=userMessage.value)


@bot.message_handler(commands=['buy'])
def handle_buy(message: Message, amount: int, server: int) -> None:

    conf = ConfigParser()
    conf.read('config.ini')
    price_stars: int = conf['Price'].getint('star')
    count_mount: int = int(amount / price_stars)

    bot.send_invoice(
        chat_id=message.chat.id,
        title="Оплата VPN",
        description=f"Продолжая, вы получите {count_mount} месяца подписки на сервере {utils.get_server_name_by_id(server)}.",
        invoice_payload=f"server:{str(server)}",  # Уникальный ID платежа (можно генерировать)
        provider_token="",  # Токен платежки (если нужен)
        currency="XTR",  # Валюта (Telegram Stars работают через USD/XTR)
        prices=[LabeledPrice(label="XTR", amount=amount)],  # 1000 = 10 Stars (1 Star = 100 единиц)
        start_parameter="start_param",  # Параметр для deep-linking
    )