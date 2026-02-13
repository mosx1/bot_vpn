"""
Модель пользователя (подписка).
"""
from sqlalchemy import Column, BIGINT, TEXT, TIMESTAMP, BOOLEAN, String, Numeric, ForeignKeyConstraint

from database.models.base import Base


class User(Base):
    __tablename__: str = 'users_subscription'

    telegram_id: Column = Column(BIGINT, primary_key=True)
    name: Column = Column(TEXT, nullable=True)
    exit_date: Column = Column(TIMESTAMP, nullable=False)
    action: Column = Column(BOOLEAN, nullable=False)
    server_link: Column = Column(TEXT, nullable=False)
    server_id: Column = Column(BIGINT, nullable=False)
    server_desired: Column = Column(String, nullable=True)
    paid: Column = Column(BOOLEAN, nullable=False)
    protocol: Column = Column(BIGINT, nullable=False)
    statistic: Column = Column(TEXT, nullable=True)
    balance: Column = Column(Numeric, nullable=True)
    invited: Column = Column(BIGINT, nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(['invited'], ['users_subscription.telegram_id']),
        ForeignKeyConstraint(['server_id'], ['servers.id'])
    )
