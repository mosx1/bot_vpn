from connect import db, bot, logging

import controllerFastApi, config

from configparser import ConfigParser

from tables import User


def renewalOfSubscription(user: User,  intervalSql: str, serverNew=None) -> bool:
    
    conf = ConfigParser()
    conf.read(config.FILE_URL + 'config.ini')

    sqlTextLink = ""

    if serverNew == None:
        serverNew = user.server_id

    if user.server_id != serverNew:
        try:

            controllerFastApi.del_users({user.telegram_id}, user.server_id)

        except Exception as e:
            
            text = "Ошибка удаления пользователей: " + str(user.telegram_id) + " с сервера: " + str(user.server_id)

            bot.send_message(
                conf['Telegram'].getint('admin_chat'),
                text
            )

            logging.error(text)

        try:

            link = controllerFastApi.add_vpn_user(user.telegram_id, serverNew)
            sqlTextLink = ", server_link='" + link + "'"

        except Exception as e:

            text: str = "Ошибка добавления пользователя: " + str(user.telegram_id) + " с сервера: " + str(user.server_id)

            bot.send_message(
                conf['Telegram'].getint('admin_chat'),
                text
            )

            logging.error(text)

    else:

        controllerFastApi.resumeUser(user.telegram_id, user.server_id)

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
                    "\nWHERE telegram_id=" + str(user.telegram_id))
        db.commit()