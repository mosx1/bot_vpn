import time, keyboards

from connect import logging, bot

from sqlalchemy import func, and_, text

from tables import User

from users.methods import get_user_by

from datetime import datetime, timedelta

from managment_user import delete_not_subscription


def check_subscription():

    second_sleep = 60

    # Notification intervals with messages (DRY principle)
    NOTIFICATION_SCHEDULE = [
        (timedelta(days=3), "Через 3 дня окончится Ваша подписка на VPN. Чтобы не потерять доступ, продлите подписку."),
        (timedelta(days=2), "Через 2 дня окончится Ваша подписка на VPN. Чтобы не потерять доступ, продлите подписку."),
        (timedelta(days=1), "Завтра в это же время окончится подписка на VPN. Чтобы не потерять доступ, продлите подписку."),
        (timedelta(hours=1), "Уже через час окончится подписка на VPN. Чтобы не потерять доступ, продлите подписку."),
        (timedelta(minutes=30), "Уже через 30 минут окончится подписка на VPN. Чтобы не потерять доступ, продлите подписку."),
        (timedelta(minutes=10), "Уже через 10 минут окончится подписка на VPN. Чтобы не потерять доступ, продлите подписку."),
        (timedelta(minutes=5), "Уже через 5 минут окончится подписка на VPN. Чтобы не потерять доступ, продлите подписку."),
        (timedelta(minutes=1), "Уже через 1 минуту окончится подписка на VPN. Чтобы не потерять доступ, продлите подписку.")
    ]

    while True:
        try:
            for interval, message_text in NOTIFICATION_SCHEDULE:
                users: list[User] = get_user_by(
                    and_(
                        User.action == True,
                        User.exit_date - text(f"INTERVAL '{interval}'") <= func.now(),
                        User.exit_date - text(f"INTERVAL '{interval}'") + text(f"INTERVAL '{second_sleep} seconds'") > func.now()
                    )
                )

                for user in users:
                    bot.send_message(
                        user.telegram_id,
                        message_text,
                        reply_markup=keyboards.getInlineExtend()
                    )

            time.sleep(60)
        except Exception:
            pass


def delete_not_subscription_tasks() -> None:

    while True:
        try:
            if datetime.now().hour == 0:
                delete_not_subscription()
                time.sleep(86400)
            time.sleep(60)  # Prevent busy loop when hour != 0
        except Exception as e:
            logging.error('thread delete_not_sub error: ' + str(e))