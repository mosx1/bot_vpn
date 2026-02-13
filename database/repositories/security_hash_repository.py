"""
Репозиторий хешей безопасности.
"""
from sqlalchemy.orm import Session
from sqlalchemy import select

from database.repositories.base_repository import BaseRepository
from database.models import SecurityHashs


class SecurityHashRepository(BaseRepository[SecurityHashs]):
    @property
    def model(self) -> type[SecurityHashs]:
        return SecurityHashs

    @property
    def pk_column(self):
        return SecurityHashs.hash

    def get_token(self) -> str:
        def _get(session: Session):
            query = select(SecurityHashs)
            result = session.execute(query)
            row = result.scalars().first()
            return row.hash if row else ""

        return self._execute_in_session(_get, commit=False)


# Синглтон
security_hash_repository = SecurityHashRepository()
