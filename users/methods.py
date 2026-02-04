from typing import Iterable

from connect import engine

from sqlalchemy.orm import Session
from sqlalchemy import select, and_, insert, update, func
from sqlalchemy.sql.elements import BinaryExpression

from tables import User, ServersTable, UserToSubscription

from servers.server_list import Country


def get_user_by_id(telegram_id: int) -> User | None:
    with Session(engine) as session:
        query = select(User).filter(User.telegram_id == telegram_id)
        return session.execute(query).scalar()
    

def get_user_by(
        filter = None, 
        limit: int | None = None,
        offset: int | None = None
) -> list[User]:
    
    with Session(engine) as session:

        if filter is None:
            filter = User.action == True

        query = (
            select(User)
            .filter(filter)
            .order_by(User.exit_date.asc())
        )

        if limit is not None: query = query.limit(limit)
        if offset is not None: query = query.offset(offset)

        return session.execute(query).scalars().all()
    

def get_user_by_country(country: Country, filter: BinaryExpression | None = None) -> Iterable[User]:

    with Session(engine) as session:
        query = (
            select(User)
            .join(
                ServersTable,
                and_(
                    ServersTable.id == User.server_id, 
                    ServersTable.country == country.value
                )
            )
        )
        if filter: query.filter(filter)

        return session.execute(query).scalars().all()
    

def add_subscription_for_user(telegram_id: int, server_link: str, server_id: str) -> None:
    """
        Добавляет запись в бд с подпиской пользователю.
    """
    with Session(engine) as session:
        query = insert(UserToSubscription).values(
            telegram_id=telegram_id,
            server_link=server_link,
            server_id=server_id
        )
        session.execute(query)
        session.commit()


def reduce_time_by(user: User, month: int) -> None:
    """
    Уменьшает кол-во месяцев на значение
    
    :param user:
    :type user: User
    :param month: кол-во месяцев уменьшения
    :type month: int
    """

    with Session(engine) as session:
        session.execute(
            update(
                User
            ).where(
                User.telegram_id == user.telegram_id
            ).values(
                exit_date = User.exit_date - func.make_interval(month=month)
            )
        )
        session.commit()