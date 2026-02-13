"""
Модель связи пользователь-подписка (несколько серверов на одного пользователя).
"""
from sqlalchemy import Column, BIGINT, TEXT, ForeignKeyConstraint

from database.models.base import Base


class UserToSubscription(Base):
    __tablename__: str = 'user_to_subscription'

    telegram_id: Column = Column(BIGINT, nullable=False)
    server_link: Column = Column(TEXT, primary_key=True)
    server_id: Column = Column(BIGINT, nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(['telegram_id'], ['users_subscription.telegram_id']),
        ForeignKeyConstraint(['server_id'], ['servers.id'])
    )
