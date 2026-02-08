from threading import Thread

from .payment import check_payments
from .managment_user import chek_subscription, delete_not_subscription_tasks
from .connect import update_connect
from .servers import health_check_task


threads = [
    Thread(target=chek_subscription),
    Thread(target=check_payments),
    Thread(target=delete_not_subscription_tasks),
    Thread(target=update_connect),
    Thread(target=health_check_task)
]

for thread in threads:
    thread.start()