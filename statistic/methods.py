import requests, json

from telebot.types import Message

from users.methods import get_user_by

from tables import User, ServersTable

from utils import get_token

from sqlalchemy.orm import Session
from sqlalchemy import Update, update, and_

from connect import engine, bot

from configparser import ConfigParser

from config import FILE_URL

from humanize import naturalsize


def get_statistics_by_server(*args) -> None:
    """
        args = (server: ServersTable)
    """
    server: ServersTable = args[0]
    conf = ConfigParser()
    conf.read(FILE_URL + 'config.ini')
    old_message: Message = bot.send_message(
        conf['Telegram']['admin_chat'],
        f"Начат сбор статистики по серверу {server.name}"
    )
    users: list[User] = get_user_by(
        and_(
            User.server_id == server.id,
            User.action == True
        )
    )
    user_ids: list[int] = [int(user.telegram_id) for user in users]
    data = {
        "user_ids": user_ids,
        "token": get_token()
    }
    response: requests.Response = requests.post(
        f"http://{server.links}/statistic",
        data = json.dumps(data)
    ).json()

    with Session(engine) as session:
        for user_id, statistic in response['link'].items():
            query: Update = (
                update(User)
                .where(User.telegram_id == user_id)
                .values(statistic = f"downlink {naturalsize(statistic['downlink'])} uplink {naturalsize(statistic['uplink'])}")
            )
            session.execute(query)
        session.commit()
    bot.edit_message_text(
        f"Завершен сбор статистики по серверу {server.name}",
        old_message.chat.id,
        old_message.id
    )