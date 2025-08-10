from connect import db, bot, logging

import network_service.controllerFastApi as controllerFastApi, config

from configparser import ConfigParser

from tables import User

from network_service.entity import NetworkServiceError


def renewalOfSubscription(user: User,  intervalSql: str, serverNew=None) -> bool:
    
    conf = ConfigParser()
    conf.read(config.FILE_URL + 'config.ini')
    admin_chat_id: int = conf['Telegram'].getint('admin_chat')

    sqlTextLink = ""

    if serverNew == None:
        serverNew = user.server_id

    if user.server_id != serverNew:
        try:

            controllerFastApi.del_users({user.telegram_id}, user.server_id)

        except Exception as e:
            
            text = "Ошибка удаления пользователей: " + str(user.telegram_id) + " с сервера: " + str(user.server_id)

            bot.send_message(
                admin_chat_id,
                text
            )

            logging.error(text)

        try:

            result_add_vpn_user: str | NetworkServiceError = controllerFastApi.add_vpn_user(user.telegram_id, serverNew)

            match result_add_vpn_user:

                case str():

                    sqlTextLink = ", server_link='" + result_add_vpn_user + "'"

                case NetworkServiceError():
                    
                    text = f"{result_add_vpn_user.caption}\nЗапрос:\n{result_add_vpn_user.response}"

                    bot.send_message(
                        admin_chat_id,
                        text
                    )
                    logging.error(text)
                    
                    return

        except Exception as e:

            text: str = "Ошибка добавления пользователя: " + str(user.telegram_id) + " с сервера: " + str(user.server_id)

            bot.send_message(
                admin_chat_id,
                text
            )

            logging.error(text)

    else:

        result_resume_user: str | NetworkServiceError = controllerFastApi.resume_user(user.telegram_id, user.server_id)

        match result_resume_user:
            
            case NetworkServiceError():

                text = f"{result_resume_user.caption}\nЗапрос:\n{result_resume_user.response}"

                bot.send_message(
                    admin_chat_id,
                    text
                )
                logging.error(text)
                
                return

    with db.cursor() as cursor:   
        cursor.execute(
            "UPDATE users_subscription" + 
            "\nSET exit_date=" +
            "\nCASE WHEN exit_date > now()" +
            "\nTHEN exit_date" + str(intervalSql) +
            "\nELSE now()" + str(intervalSql) +
            "\nEND,action=True, paid=True" + 
            sqlTextLink + 
            ", server_id = '" + str(serverNew) + "'" +
            ", protocol=" + str(config.DEFAULTPROTOCOL) + 
            "\nWHERE telegram_id=" + str(user.telegram_id)
        )
        db.commit()