from threading import Thread

from servers.methods import get_server_list

from tables import ServersTable

from statistic.methods import get_statistics_by_server


def start_statistic() -> None:
    
    servers: list[ServersTable] = get_server_list()

    for server in servers:
        get_statistic_task = Thread(
            target=get_statistics_by_server,
            args=(server,)
        )
        get_statistic_task.start()