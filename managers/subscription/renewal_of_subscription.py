from connect import db, bot, logging

import controllerFastApi, config

from configparser import ConfigParser


def renewalOfSubscription(userId, serverId, intervalSql: str, serverNew=None) -> bool:
    
    conf = ConfigParser()
    conf.read(config.FILE_URL + 'config.ini')

    sqlTextLink = ""

    if serverNew == None:
        serverNew = serverId

    if serverId != serverNew:
        try:

            controllerFastApi.del_users({userId}, serverId)

        except Exception as e:
            
            text = "Ошибка удаления пользователей: " + str(userId) + " с сервера: " + str(serverId)

            bot.send_message(
                conf['Telegram'].getint('admin_chat'),
                text
            )

            logging.error(text)

        try:

            link = controllerFastApi.add_vpn_user(userId, serverNew)
            sqlTextLink = ", server_link='" + link + "'"

        except Exception as e:

            text: str = "Ошибка добавления пользователя: " + str(userId) + " с сервера: " + str(serverId)

            bot.send_message(
                conf['Telegram'].getint('admin_chat'),
                text
            )

            logging.error(text)

    else:

        controllerFastApi.resumeUser(userId, serverId)

    with db.cursor() as cursor:   
        cursor.execute("UPDATE users_subscription" + 
                    "\nSET exit_date=" +
                    "\nCASE WHEN exit_date > now()" +
                    "\nTHEN exit_date" + str(intervalSql) +
                    "\nELSE now()" + str(intervalSql) +
                    "\nEND,action=True, paid=True" + 
                    sqlTextLink + 
                    ", server_id = '" + str(serverNew) + "'" +
                    ", protocol=" + str(config.DEFAULTPROTOCOL) + 
                    "\nWHERE telegram_id=" + str(userId))
        db.commit()