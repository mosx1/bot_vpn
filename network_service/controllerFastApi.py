import requests, utils, json, time

from connect import logging

from .entity import NetworkServiceError


def add_vpn_user(
     userId: int,
     server: int,
     token: str = utils.get_token()
) -> str | NetworkServiceError:
     """
          Создает пользователя в xray
     """

     logging.info(
          'Создание пользователя ' + str(userId) + ' на сервере ' + utils.getUrlByIdServer(server)
     )

     try:
          response = requests.get(
               "http://{}/add?user_id={}&token={}".format(
                    utils.getUrlByIdServer(server),
                    userId,
                    token
               ),
               timeout=20
          )
     except Exception as e:
          logging.error(str(e))

     response = response.json()
     if response["success"]:
          return response["link"]

     return NetworkServiceError(
          caption="Ошибка в запросе на добавление пользователя",
          response=str(response)
     )



def suspend_users(
     user_ids: set[int],
     server: int,
     token: str = utils.get_token()
) -> bool | NetworkServiceError:
     """
          Приостонавливает пользователя в xray
     """
     data = {
          "token": token,
          "user_ids": list(user_ids)
     }
     response = requests.post(
          "http://{}/suspend".format(
               utils.getUrlByIdServer(server)
          ),
          data = json.dumps(data),
          timeout=20
          ).json()

     if "success" in response and response["success"]:
          return response["success"]

     return NetworkServiceError(
          caption="Ошибка в запросе на приостановление пользователя",
          response=str(response)
     )



def resume_user(
     userId: int,
     server: int,
     token: str = utils.get_token()     
) -> str | NetworkServiceError:
     """
          Возобновляет доступ пользователя к xray
     """

     logging.info(
          'Возобновление пользователя ' + str(userId) + ' на сервере ' + utils.getUrlByIdServer(server)
     )

     response = requests.get(
          "http://{}/resume?userId={}&token={}".format(
               utils.getUrlByIdServer(server),
               userId,
               token
               ),
          timeout=20
          ).json()
     if response["success"]:
          return response["success"]

     return NetworkServiceError(
          caption="Ошибка в запросе на восстановление пользователя",
          response=str(response)
     )



def del_users(
     user_ids: set[int],
     server: int,
     token: str = utils.get_token()
) -> bool:
    """
        Удаляет пользователей с сервера
    """

    data = {
         "token": token,
         "user_ids": list(user_ids)
    }
    try:
     response = requests.post(
          "http://{}/del".format(
               utils.getUrlByIdServer(server)
          ),
          data = json.dumps(data),
          timeout=20
          ).json()
    except Exception as e:
          logging.error(str(e))

    return str(response)


