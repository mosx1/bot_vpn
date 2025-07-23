from typing import Iterable

from connect import engine

from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.sql.elements import BinaryExpression

from tables import User, ServersTable

from servers.server_list import Country


def get_user_by_id(telegram_id: int) -> User:
    with Session(engine) as session:
        query = select(User).filter(User.telegram_id == telegram_id)
        return session.execute(query).scalar()
    

def get_user_by(
        filter: BinaryExpression | None = None, 
        limit: int | None = None,
        offset: int | None = None
) -> list[User]:
    
    with Session(engine) as session:

        query = select(User)

        if filter is not None: query = query.filter(filter)
        if limit is not None: query = query.limit(limit)
        if offset is not None: query = query.offset(offset)

        return session.execute(query).scalars().all()
    

def get_user_by_country(country: Country, filter: BinaryExpression | None = None) -> Iterable[User]:
    with Session(engine) as session:
        query = (
            select(User)
            .join(
                ServersTable,
                (ServersTable.id == User.server_id) & (ServersTable.country == country.value)
            )
            .filter(filter)
        )
        return session.execute(query).scalars().all()