from threading import Thread

from .managment_user import check_subscription
from .connect import update_connect
from .servers import health_check_task, backup_server_config_task


threads = [
    Thread(target=check_subscription),
    Thread(target=update_connect),
    Thread(target=health_check_task),
    Thread(target=backup_server_config_task)
]

for thread in threads:
    thread.start()