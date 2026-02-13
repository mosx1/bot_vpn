"""
Модели серверов и стран.
"""
from sqlalchemy import Column, INTEGER, TEXT, BOOLEAN, VARCHAR, text

from database.models.base import Base


class ServersTable(Base):
    __tablename__: str = 'servers'

    id: Column = Column(INTEGER, primary_key=True)
    links: Column = Column(TEXT, nullable=False)
    country: Column = Column(INTEGER, nullable=False)
    name: Column = Column(TEXT, nullable=False)
    speed: Column = Column(INTEGER)
    answers: Column = Column(BOOLEAN, nullable=False, server_default=text("true"))


class CountryTable(Base):
    __tablename__: str = 'country'

    id: Column = Column(INTEGER, primary_key=True)
    name: Column = Column(VARCHAR(64), nullable=False)
