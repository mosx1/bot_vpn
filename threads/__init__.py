from .payment import check_payments

from threading import Thread

check_payments_thread = Thread(target=check_payments)

check_payments_thread.start()