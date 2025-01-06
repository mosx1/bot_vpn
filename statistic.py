import config, time

from controllerFastApi import getStat
from connect import db, bot
from psycopg2.extras import DictCursor
from enums.server_list import Servers


def updateStatistic():
    old_message = bot.send_message(config.ADMINCHAT, 'Сбор статистики')
    with db.cursor(cursor_factory=DictCursor) as cursor:
        # for serverId in Servers:
        stat = getStat(Servers.niderlands2.value)
        
        cursor.execute("SELECT telegram_id FROM users_subscription WHERE server_id = " + str(Servers.niderlands2.value))
        for c in cursor.fetchall():
            # {"6974679639":{"Uploaded":": 2.73 M","Downloaded":": 11.64 M"}
            if str(c['telegram_id']) in stat:
                textStat = ', '.join(f'{k} {v}' for k, v in stat[str(c['telegram_id'])].items())
                cursor.execute("UPDATE users_subscription SET statistic = '" + textStat + "' WHERE telegram_id = " + str(c["telegram_id"]))
        db.commit()
    bot.send_message(config.ADMINCHAT, reply_to_message_id=old_message.id, text='Статистика готова')