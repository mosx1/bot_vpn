from connect import engine

from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, text
from sqlalchemy.sql.elements import BinaryExpression

from tables import ServersTable, CountryTable, User

from servers.server_list import Country, Servers

from configparser import ConfigParser

from config import FILE_URL


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
    

def get_very_free_server(country: Country | None = None) -> int:
    """
        Возвращает менее загруженный сервер по стране
        Если страна не передана - ищет по всем странам
    """

    conf = ConfigParser()
    conf.read(FILE_URL + 'config.ini')

    with Session(engine) as session:
        # query = (
        #     select(
        #         func.count().label('count'),
        #         ServersTable.id
        #     )
        #     .select_from(ServersTable)
        #     .join(
        #         User,
        #         and_(
        #             User.server_id == ServersTable.id,
        #             User.action == True
        #         ), 
        #         isouter=True
        #     )
        # )

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
                    ServersTable.id != Servers.niderlands2.value,
                    ServersTable.id != Servers.finland1.value
                )
            )

        query = (
            query
            .group_by(ServersTable.id)
            .order_by(text('count ASC'))
            .limit(1)
        )
        result = session.execute(query).one()
        
        return result.id