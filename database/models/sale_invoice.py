"""
Модель счетов на оплату в процессе.
"""
from sqlalchemy import Column, BIGINT, TEXT, SMALLINT, TIMESTAMP, func, ForeignKeyConstraint

from database.models.base import Base


class SaleInvoicesInProgress(Base):
    __tablename__: str = 'sale_invoices_in_progress'

    id: Column = Column(BIGINT, primary_key=True)
    telegram_id: Column = Column(BIGINT, nullable=False)
    label: Column = Column(TEXT, nullable=False)
    server_id: Column = Column(BIGINT, nullable=False)
    month_count: Column = Column(SMALLINT, nullable=False)
    message_id: Column = Column(BIGINT, nullable=False)
    chat_id: Column = Column(BIGINT, nullable=False)
    create_date: Column = Column(TIMESTAMP, nullable=False, server_default=func.now())

    __table_args__ = (
        ForeignKeyConstraint(['telegram_id'], ['users_subscription.telegram_id']),
        ForeignKeyConstraint(['server_id'], ['servers.id'])
    )
