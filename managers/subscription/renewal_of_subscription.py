from connect import bot, logging

from network_service import controllerFastApi
from network_service.entity import NetworkServiceError

from database import User, get_server_name_by_id, update_user_renewal

from configparser import ConfigParser


def renewalOfSubscription(user: User, intervalSql: str, serverNew=None) -> None:
    
    conf = ConfigParser()
    conf.read('config.ini')
    admin_chat_id: int = conf['Telegram'].getint('admin_chat')

    if not serverNew:
        serverNew = user.server_id

    if user.server_id != serverNew and intervalSql != " + INTERVAL '0 months'": #костыль для ускорения
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
                update_user_renewal(
                    telegram_id=user.telegram_id,
                    interval_sql=intervalSql,
                    server_link=result_add_vpn_user,
                    server_id=serverNew,
                    protocol=int(conf['BaseConfig'].get('default_protocol'))
                )


            case NetworkServiceError():
                
                text = f"{result_add_vpn_user.caption}\nОтвет сервера:\n{result_add_vpn_user.response}"

                bot.send_message(
                    admin_chat_id,
                    text
                )
                logging.error(text)
                
                return

    except Exception as e:
        
        text: str = "Ошибка добавления пользователя: " + str(user.telegram_id) + " на сервер: " + get_server_name_by_id(user.server_id)

        bot.send_message(
            admin_chat_id,
            text + str(e)
        )

        logging.error(text + str(e))

        return

    