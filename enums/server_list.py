from enum import Enum

class Servers(Enum):
    
    usa = 1
    deutsche = 2
    niderlands2 = 3

class ServerUrl(Enum):

    usa = "80.209.243.179:8081"
    deutsche = "109.120.140.150:8081"
    niderlands2 = "46.17.103.204:8081"


def getServerNameById(server: int) -> str:
    
    for i in Servers:
        if i.value == server:
            return i.name