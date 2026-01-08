from threading import Thread

from .payment import check_payments
from .managment_user import chek_subscription, delete_not_subscription_tasks
from .connect import update_connect


check_subscription_thread = Thread(target=chek_subscription)
check_payments_thread = Thread(target=check_payments)
del_not_sub_thread = Thread(target=delete_not_subscription_tasks)
update_tread = Thread(target=update_connect)


check_subscription_thread.start()
check_payments_thread.start()
del_not_sub_thread.start()
update_tread.start()