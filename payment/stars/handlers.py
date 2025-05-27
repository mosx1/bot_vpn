from telebot import TeleBot
from telebot.types import LabeledPrice, Message


def register_message_handlers(bot: TeleBot) -> None:

    @bot.message_handler(commands=['buy'])
    def handle_buy(message: Message) -> None:
        # Отправляем инвойс (платежное меню)
        bot.send_invoice(
            chat_id=message.chat.id,
            title="Оплата VPN",
            description="Описание услуги",
            invoice_payload="test_payload",  # Уникальный ID платежа (можно генерировать)
            provider_token="",  # Токен платежки (если нужен)
            currency="XTR",  # Валюта (Telegram Stars работают через USD/XTR)
            prices=[LabeledPrice(label="XTR", amount=1)],  # 1000 = 10 Stars (1 Star = 100 единиц)
            start_parameter="start_param",  # Параметр для deep-linking
            # photo_url="https://example.com/item.jpg",  # Картинка товара (опционально)
        )

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
        bot.send_message(
            message.chat.id,
            "✅ **Оплата прошла успешно!** Спасибо за покупку!\n"
            f"ID платежа: `{message.successful_payment.telegram_payment_charge_id}`"
        )