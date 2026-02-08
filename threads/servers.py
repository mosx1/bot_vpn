import time

from servers.methods import check_answers_servers

def health_check_task():
    while True:
        check_answers_servers()
        time.sleep(60)