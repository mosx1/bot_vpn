import config

from enum import Enum

class Comands(Enum):
    
    adminPanel: str = config.ADMINPASSWORD
    resubusa: str = 'rsu'
    statistic: str = "stat"
    restart: str = "restart"
    actionUsersCount: str = "action_users_count"
    start: str = "start"
    checkSubscription: str = 'checkSubscription'