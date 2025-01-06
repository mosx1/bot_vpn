import requests, utils, utils

def add_vpn_user(userId: str, server: int):
    """
        Создает пользователя в xray
    """
    
    response = requests.get(
         "http://{}/597730754/add/{}".format(
              utils.getUrlByIdServer(server),
              userId
              )
         ).json()
    if response["success"]:
         return response["link"]
    
    return response["success"]



def suspendUser(userId: str, server: int) -> bool:
    """
        Приостонавливает пользователя в xray
    """
    response = requests.get(
         "http://{}/597730754/suspend/{}".format(
              utils.getUrlByIdServer(server), 
              userId
              )
         ).json()
    
    if response["success"]:
         return response["success"]
    
    return response["success"]



def resumeUser(userId: str, server: int):
    """
        Возобновляет доступ пользователя к xray
    """
    response = requests.get(
         "http://{}/597730754/resume/{}".format(
              utils.getUrlByIdServer(server),
              userId
              )
         ).json()
    if response["success"]:
         return response["success"]
    
    return response["success"]



def delUser(userId: str, server: int):
    """
        Удаляет пользователя с сервера
    """
    response = requests.get(
         "http://{}/597730754/del/{}".format(
              utils.getUrlByIdServer(server),
              userId
              )
         ).json()
    if response["success"]:
         return response["success"]
    
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