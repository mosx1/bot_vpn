import time

from connect import logging

from servers.methods import health_check, get_server_list, update_answers_servers

from typing import Sequence

from tables import ServersTable

def health_check_task():
    while True:
        
        servers: Sequence[ServersTable] = get_server_list()
        for server in servers:
            answers = False
            code = health_check(f"http://{server.links}/config")
            if code == 200:
                answers = True
            update_answers_servers(server.id, answers)
            logging.info(f"health_chech_server: {str(server.name)} value: {str(answers)}")
            print(f"health_chech_server: {str(server.name)} value: {str(answers)}")
        
        time.sleep(60)
