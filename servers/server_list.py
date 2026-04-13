from enum import Enum

class Servers(Enum):

    niderlands2: int = 3
    deutshe4: int = 6
    deutshe5: int = 7


class Country(Enum):
    
    niderlands: int = 1
    deutsche: int = 2


class Strategy(Enum):

    easy_xray: str = 1
    x_ui: str = 2