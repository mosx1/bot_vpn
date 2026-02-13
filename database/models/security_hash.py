"""
Модель хешей безопасности.
"""
from sqlalchemy import Column, TEXT, TIME, func

from database.models.base import Base


class SecurityHashs(Base):
    __tablename__: str = 'securityhashs'

    hash: Column[str] = Column(TEXT, primary_key=True)
    data: Column = Column(TIME(timezone=True), nullable=False, default=func.now())
