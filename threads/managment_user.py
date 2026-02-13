import time, keyboards

from connect import logging, bot, engine

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, text

from database import User

from users.methods import get_user_by

from datetime import datetime

from managment_user import del_users, delete_not_subscription


def chek_subscription():

    second_sleep = 60

    while True:
        try:
            with Session(engine) as session:
                data = session.execute(
                    text(
                        "SELECT server_id, array_agg(DISTINCT telegram_id) as telegram_ids" +
                        "\nFROM users_subscription" +
                        "\nWHERE action = True AND exit_date < now()" +
                        "\nGROUP BY server_id"
                    )
                )
                server_to_users_for_delete = data.fetchall()
                
                for server_to_users_for_delete_item in server_to_users_for_delete:
                    
                    del_users(
                        set(server_to_users_for_delete_item.telegram_ids),
                        int(server_to_users_for_delete_item.server_id)
                    )

            users: list[User] = get_user_by(
                and_(
                    User.action == True,
                    User.exit_date - text("INTERVAL '3 days'") <= func.now(),
                    User.exit_date - text("INTERVAL '3 days'") + text(f"INTERVAL '{second_sleep} seconds'") > func.now()
                )
            )

            for user in users:

                bot.send_message(
                    user.telegram_id,
                    "Через 3 дня окончится Ваша подписка на VPN. Чтобы не потерять доступ, продлите подписку.",
                    reply_markup=keyboards.getInlineExtend()
                )

            users: list[User] = get_user_by(
                and_(
                    User.action == True,
                    User.exit_date - text("INTERVAL '2 days'") <= func.now(),
                    User.exit_date - text("INTERVAL '2 days'") + text(f"INTERVAL '{second_sleep} seconds'") > func.now()
                )
            )

            for user in users:

                bot.send_message(
                    user.telegram_id,
                    "Через 2 дня окончится Ваша подписка на VPN. Чтобы не потерять доступ, продлите подписку.",
                    reply_markup=keyboards.getInlineExtend()
                )
            
            users: list[User] = get_user_by(
                and_(
                    User.action == True,
                    User.exit_date - text("INTERVAL '1 days'") <= func.now(),
                    User.exit_date - text("INTERVAL '1 days'") + text(f"INTERVAL '{second_sleep} seconds'") > func.now()
                )
            )

            for user in users:

                bot.send_message(
                    user.telegram_id,
                    "Завтра в это же время окончится подписка на VPN. Чтобы не потерять доступ, продлите подписку.",
                    reply_markup=keyboards.getInlineExtend()
                )
            
            users: list[User] = get_user_by(
                and_(
                    User.action == True,
                    User.exit_date - text("INTERVAL '1 hours'") <= func.now(),
                    User.exit_date - text("INTERVAL '1 hours'") + text(f"INTERVAL '{second_sleep} seconds'") > func.now()
                )
            )

            for user in users:

                bot.send_message(
                    user.telegram_id,
                    "Уже через час окончится подписка на VPN. Чтобы не потерять доступ, продлите подписку.",
                    reply_markup=keyboards.getInlineExtend()
                )

            time.sleep(60)
        except Exception as e:
            logging.error('tread check_subscription error: ' + str(e))


def delete_not_subscription_tasks() -> None:

    while True:
        try:
            if datetime.hour == 0:
                delete_not_subscription()
                time.sleep(86400)
        except Exception as e:
            logging.error('tread delete_not_sub error: ' + str(e))