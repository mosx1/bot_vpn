from connect import engine

from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.sql.elements import BinaryExpression

from tables import ServersTable, CountryTable


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