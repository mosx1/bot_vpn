"""
Базовый абстрактный репозиторий.

Пример использования:

    from database.models import ServersTable

    class ServerRepository(BaseRepository[ServersTable]):
        @property
        def model(self) -> type[ServersTable]:
            return ServersTable

        @property
        def pk_column(self):
            return ServersTable.id
"""
from abc import ABC, abstractmethod
from typing import Any, Callable, TypeVar, Generic

from sqlalchemy import select, update, delete
from sqlalchemy.orm import Session

from database.connection import engine


ModelT = TypeVar("ModelT")


class BaseRepository(ABC, Generic[ModelT]):
    """Абстрактный базовый класс репозитория с CRUD-операциями."""

    def __init__(self) -> None:
        self._engine = engine

    @property
    @abstractmethod
    def model(self) -> type[ModelT]:
        """Модель SQLAlchemy, с которой работает репозиторий."""
        ...

    @property
    @abstractmethod
    def pk_column(self):
        """Колонка первичного ключа модели."""
        ...

    def _session(self) -> Session:
        """Возвращает новую сессию."""
        return Session(self._engine)

    def _execute_in_session(self, operation: Callable[[Session], Any], *, commit: bool = True) -> Any:
        """Выполняет операцию в рамках сессии с автоматическим commit/rollback."""
        with self._session() as session:
            try:
                result = operation(session)
                if commit:
                    session.commit()
                return result
            except Exception:
                session.rollback()
                raise

    def get_by_id(self, pk_value) -> ModelT | None:
        """Получить сущность по первичному ключу."""
        def _get(session: Session):
            query = select(self.model).where(self.pk_column == pk_value)
            return session.execute(query).scalars().one_or_none()

        return self._execute_in_session(_get, commit=False)

    def get_all(self, *, limit: int | None = None, offset: int | None = None) -> list[ModelT]:
        """Получить все сущности с опциональной пагинацией."""
        def _get_all(session: Session):
            query = select(self.model)
            if limit is not None:
                query = query.limit(limit)
            if offset is not None:
                query = query.offset(offset)
            return list(session.execute(query).scalars().all())

        return self._execute_in_session(_get_all, commit=False)

    def add(self, entity: ModelT) -> ModelT:
        """Добавить сущность."""
        def _add(session: Session):
            session.add(entity)
            session.flush()
            return entity

        return self._execute_in_session(_add)

    def add_many(self, entities: list[ModelT]) -> None:
        """Добавить несколько сущностей."""
        def _add_many(session: Session):
            session.add_all(entities)

        self._execute_in_session(_add_many)

    def update(self, pk_value: Any, **values: Any) -> bool:
        """Обновить сущность по первичному ключу. Возвращает True при успехе."""
        if not values:
            return False

        def _update(session: Session):
            result = session.execute(
                update(self.model).where(self.pk_column == pk_value).values(**values)
            )
            return result.rowcount > 0

        return self._execute_in_session(_update)

    def delete(self, pk_value) -> bool:
        """Удалить сущность по первичному ключу. Возвращает True при успехе."""
        def _delete(session: Session):
            result = session.execute(delete(self.model).where(self.pk_column == pk_value))
            return result.rowcount > 0

        return self._execute_in_session(_delete)
