"""
Модель конфигов серверов.
"""
from sqlalchemy import Column, BIGINT, ForeignKeyConstraint
from sqlalchemy.dialects.postgresql import JSONB

from database.models.base import Base


class ConfigsServers(Base):
    __tablename__: str = 'configs_servers'

    id = Column(BIGINT, primary_key=True)
    server_id = Column(BIGINT, nullable=False)
    config = Column(JSONB)

    __table_args__ = (
        ForeignKeyConstraint(['server_id'], ['servers.id']),
    )
