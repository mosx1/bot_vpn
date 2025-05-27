from connect import engine

from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.sql.elements import BinaryExpression

from tables import User


def get_user_by_id(telegram_id: int) -> User:
    with Session(engine) as session:
        query = select(User).filter(User.telegram_id == telegram_id)
        return session.execute(query).scalar()
    

def get_user_by(filter: BinaryExpression | None = None) -> list[User]:
    with Session(engine) as session:
        query = select(User).filter(filter)
        return session.execute(query).scalars().all()