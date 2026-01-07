import config

from enum import Enum

from configparser import ConfigParser

class Comands(Enum):
    
    resubusa: str = 'rsu'
    statistic: str = "stat"
    restart: str = "restart"
    actionUsersCount: str = "action_users_count"
    start: str = "start"
    checkSubscription: str = 'checkSubscription'

    @property
    def admin_panel(self) -> str:

        conf = ConfigParser()
        conf.read('config.ini')

        return conf['Telegram'].get('admin_password')