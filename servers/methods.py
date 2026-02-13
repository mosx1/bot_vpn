import gevent.monkey
gevent.monkey.patch_socket()

import requests
import gevent

from typing import Tuple

from database import (
    get_server_list,
    get_country_list,
    get_server_name_by_id,
    get_very_free_server as _get_very_free_server,
    get_info_all_servers,
    get_info_servers,
    update_answers_servers,
)



from database.models import ServersTable

from connect import logging

from servers.server_list import Country, Servers

from sqlalchemy.orm import Session
from sqlalchemy import Sequence


def get_very_free_server(country: Country | None = None, exclude_server_id: int | None = None) -> int:
    """Возвращает менее загруженный сервер. Обёртка для обратной совместимости."""
    country_value = country.value if country else None
    return _get_very_free_server(country_value, exclude_server_id)


def health_check(url: str) -> int:
    try:
        res = requests.get(url, timeout=5)
        return res.status_code
    except Exception:
        pass


def update_answers_servers_wrapper(server_id: int, answers: bool) -> None:
    """Обёртка для обратной совместимости."""
    update_answers_servers(server_id, answers)


def health_check_and_update_answers(server: ServersTable):
    code = health_check(f"http://{server.links}/config")
    answers = bool(code == 200)
    update_answers_servers(server.id, answers)
    logging.info(f"health_chech_server: {str(server.name)} value: {answers}")
    print(f"health_chech_server: {str(server.name)} value: {answers}")


def check_answers_servers():
    servers: Sequence[ServersTable] = get_server_list()
    gevent.joinall([gevent.spawn(health_check_and_update_answers, server) for server in servers])


if __name__ == "__main__":
    health_check('http://de8.kuzmos.ru:8081/config')
