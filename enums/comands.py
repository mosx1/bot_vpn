import config

from enum import Enum

class Comands(Enum):
    
    adminPanel = config.ADMINPASSWORD
    resubusa = 'rsu'
    statistic = "stat"
    restart = "restart"
    actionUsersCount = "action_users_count"
    start = "start"