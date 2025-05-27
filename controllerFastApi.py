import requests, utils, utils, json


def add_vpn_user(
     userId: int,
     server: int,
     token: str = utils.get_token()
):
    """
        Создает пользователя в xray
    """
    
    response = requests.get(
         "http://{}/add?user_id={}&token={}".format(
              utils.getUrlByIdServer(server),
              userId,
              token
              )
         ).json()
    if response["success"]:
         return response["link"]
    
    return response["error"]



def suspendUser(
     userId: int,
     server: int,
     token: str = utils.get_token()
) -> bool:
    """
        Приостонавливает пользователя в xray
    """
    response = requests.get(
         "http://{}/suspend?userId={}&token={}".format(
              utils.getUrlByIdServer(server), 
              userId,
              token
              )
         ).json()
    
    if response["success"]:
         return response["success"]
    
    return response["error"]



def resumeUser(
     userId: int,
     server: int,
     token: str = utils.get_token()     
):
    """
        Возобновляет доступ пользователя к xray
    """
    response = requests.get(
         "http://{}/resume?userId={}&token={}".format(
              utils.getUrlByIdServer(server),
              userId,
              token
              )
         ).json()
    if response["success"]:
         return response["success"]
    
    return response["error"]



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
    response = requests.post(
         "http://{}/del".format(
              utils.getUrlByIdServer(server)
         ),
         data = json.dumps(data)
         ).json()

    return response["success"]



def getStat(server: int) -> dict:
     """
          Запрос статистики по серверу
     """
     response = requests.get(
         "http://{}/597730754/stat".format(
              utils.getUrlByIdServer(server)
              )
         ).json()
     
     return response