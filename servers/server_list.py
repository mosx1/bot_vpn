from enum import Enum

class Servers(Enum):

    deutsche: int = 2
    deutsche2: int = 1
    deutsche3: int = 4
    niderlands2: int = 3



class ServerName(Enum):

    deutsche: str = "Германия",
    niderlands2: str = "Нидерланды"


class Country(Enum):
    
    niderlands: int = 1
    deutsche: int = 2


