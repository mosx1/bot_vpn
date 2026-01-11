from typing import Tuple
from connect import engine

from sqlalchemy.orm import Session
from sqlalchemy import Row, Sequence, select, func, and_, text
from sqlalchemy.sql.elements import BinaryExpression

from tables import ServersTable, CountryTable, User

from servers.server_list import Country, Servers

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
    

def get_very_free_server(country: Country | None = None, exclude_server_id: int | None = None) -> int:
    """
        Возвращает менее загруженный сервер по стране
        Если страна не передана - ищет по всем странам
    """

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
        )
        
        if country:
            query = query.filter(ServersTable.country == country.value)
        else:
            query = query.filter(
                and_(
                    ~ServersTable.id.in_(
                        [
                            Servers.niderlands2.value
                        ]
                    )
                )
            )

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
                    func.count().label("count"),
                    func.count().filter(User.paid == True).label("count_pay"),
                    (func.count() / conf['BaseConfig'].getfloat('coefficient_load_servers') / ServersTable.speed * 100).label('load')
                ).join(
                    User, ServersTable.id == User.server_id
                ).filter(
                    User.action == True
                ).group_by(
                    ServersTable.name,
                    ServersTable.speed
                )
            ).order_by(text('count_pay DESC'))
            
            return session.execute(query).all()