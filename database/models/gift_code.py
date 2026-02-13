"""
Модель подарочных кодов.
"""
from sqlalchemy import Column, TEXT, SMALLINT, ForeignKeyConstraint

from database.models.base import Base


class GiftCodes(Base):
    __tablename__: str = 'gift_codes'

    code: Column[str] = Column(TEXT, primary_key=True)
    month: Column[int] = Column(SMALLINT, nullable=False)
