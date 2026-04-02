import gevent.monkey, utils
gevent.monkey.patch_socket()

import requests, gevent

from typing import Tuple

from connect import engine, logging

from sqlalchemy.orm import Session
from sqlalchemy import Row, Sequence, select, func, and_, text, update
from sqlalchemy.sql.elements import BinaryExpression

from tables import ServersTable, CountryTable, User, MTProxyConfigs

from servers.server_list import Country

from configparser import ConfigParser


def get_server_list(filter: BinaryExpression | None = None) -> list[ServersTable]:
    with Session(engine) as session:
        query = select(ServersTable)
        if filter:
            query.filter(filter)
        return session.execute(query).scalars().all()
    

def get_country_list(filter: BinaryExpression | None = None) -> list[CountryTable]:
    with Session(engine) as session:
        query = select(CountryTable)
        if filter:
            query.filter(filter)
        return session.execute(query).scalars().all()
    

def get_server_name_by_id(server_id: int) -> str:
    
    query = select(ServersTable).filter(ServersTable.id == server_id)

    with Session(engine) as session:
        data: ServersTable | None = session.execute(query).scalar()
        if data:
            return data.name
        return "Неизвестное наименование сервера"

def get_server_by_id(server_id: int) -> ServersTable:
    
    query = select(ServersTable).filter(ServersTable.id == server_id)

    with Session(engine) as session:
        data: ServersTable | None = session.execute(query).scalar()
        if data:
            return data
        return "Неизвестное наименование сервера"
    

def get_very_free_server(country: Country | None = None, exclude_server_id: int | None = None, wl: bool = False) -> int:
    """
        Возвращает менее загруженный сервер по стране
        Если страна не передана - ищет по всем странам
    """
    # check_answers_servers()

    conf = ConfigParser()
    conf.read('config.ini')

    with Session(engine) as session:

        query = (
            select(
                (func.count() / conf['BaseConfig'].getfloat('coefficient_load_servers') / ServersTable.speed).label('count'),
                ServersTable.id
            )
            .select_from(ServersTable)
            .join(
                User,
                and_(
                    User.server_id == ServersTable.id,
                    User.action == True
                ), 
                isouter=True
            )
            .filter(
                ServersTable.answers == True,
                ServersTable.is_wl == wl
            )
        )
        
        if country:
            query = query.filter(ServersTable.country == country.value)

        if exclude_server_id:
            query = query.filter(ServersTable.id != exclude_server_id)

        query = (
            query
            .group_by(ServersTable.id)
            .order_by(text('count ASC'))
            .limit(1)
        )
        result = session.execute(query).one()
        
        return result.id
    

def get_info_all_servers() -> Row[Tuple]:
    """
        Информация по всем серверам вместе
    """
    conf = ConfigParser()
    conf.read('config.ini')
    
    with Session(engine) as session:
            
            query = select(
                    func.count().label("count"),
                    func.count().filter(User.paid == True).label("count_pay")
                ).filter(User.action == True)
            
            return session.execute(query).one()


def get_info_servers() -> Sequence[Row[Tuple]]:
    """
        Информация отдельно по каждому серверу
    """
    conf = ConfigParser()
    conf.read('config.ini')
    
    with Session(engine) as session:
            
            query = (
                select(
                    ServersTable.name.label("name"),
                    ServersTable.answers,
                    func.count().label("count"),
                    func.count().filter(User.paid == True).label("count_pay"),
                    (func.count() / conf['BaseConfig'].getfloat('coefficient_load_servers') / ServersTable.speed * 100).label('load')
                ).join(
                    User, ServersTable.id == User.server_id
                ).filter(
                    User.action == True
                ).group_by(
                    ServersTable.name,
                    ServersTable.speed,
                    ServersTable.answers
                )
            ).order_by(text('count_pay DESC'))
            
            return session.execute(query).all()


def health_check(url: str) -> int:
    try:
        res = requests.get(url, timeout=5)
        return res.status_code
    except Exception:
        pass


def update_answers_servers(server_id: int, answers: bool) -> None:
    with Session(engine) as session:
        session.execute(
            update(
                ServersTable
            ).where(
                ServersTable.id == server_id
            ).values(
                answers=answers
            )
        )
        session.commit()


def health_check_and_update_answers(server: ServersTable):
    code = health_check(f"http://{server.links}/config")
    answers = bool(code == 200)
    update_answers_servers(server.id, answers)


def check_answers_servers():
    servers: Sequence[ServersTable] = get_server_list()
    gevent.joinall([gevent.spawn(health_check_and_update_answers, server) for server in servers])


def get_url_mtproto(server_id: int) -> str:
    with Session(engine) as session:
        mtproxyconfig = session.execute(
            select(MTProxyConfigs).where(MTProxyConfigs.server_id == server_id)
        ).scalar_one()
        
        return mtproxyconfig.url


def run_backup_server_config(url: int) -> None:
    token = utils.get_token()
    try:
        requests.get(f"http://{url}/backup_config?token={token}")
    except Exception as e:
        logging.error(f"Ошибка при выполнении запроса на резервное копирование конфигурации сервера {url}: {e}")