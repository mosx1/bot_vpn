"""Сообщения пользователю с inline-клавиатурой управления подпиской (vpn-webapp /sub/*)."""

from __future__ import annotations

from datetime import datetime

from telebot import TeleBot
from telebot.types import Message

import utils
from enums.parse_mode import ParseMode
from keyboards import get_inline_web_page
from tables import User
from users.methods import get_jwt_by_id, get_user_by_id


def send_subscription_manage_message(
    bot: TeleBot,
    telegram_id: int,
    text: str,
    *,
    user: User | None = None,
    parse_mode: str | None = None,
    pin: bool = False,
    disable_notification: bool = False,
) -> Message | None:
    """
    Отправляет текст и клавиатуру с WebApp/URL и callback на эндпоинты vpn-webapp (/sub/*).
    """
    resolved_user = user if user is not None else get_user_by_id(telegram_id)
    if not resolved_user:
        return None

    token = get_jwt_by_id(telegram_id)
    sent = bot.send_message(
        telegram_id,
        text,
        parse_mode=parse_mode,
        reply_markup=get_inline_web_page(token, resolved_user),
        disable_notification=disable_notification,
    )
    if pin and sent:
        bot.pin_chat_message(
            sent.chat.id,
            sent.message_id,
            disable_notification=True,
        )
    return sent


def format_subscription_expire_line(expire_timestamp: int | None) -> str:
    if not expire_timestamp:
        return "Срок действия подписки не удалось определить."
    expire_dt = datetime.fromtimestamp(expire_timestamp)
    return f"Подписка активна до: {utils.replaceMonthOnRuText(expire_dt)}"
