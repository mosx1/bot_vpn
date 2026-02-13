"""
Репозиторий пользователей.
"""
from typing import Iterable

from sqlalchemy.orm import Session
from sqlalchemy import select, and_, insert, update, delete, text, func
from sqlalchemy.sql.elements import BinaryExpression

from database.repositories.base_repository import BaseRepository
from database.models import User, ServersTable


class UserRepository(BaseRepository[User]):
    @property
    def model(self) -> type[User]:
        return User

    @property
    def pk_column(self):
        return User.telegram_id

    def get_user_by_id(self, telegram_id: int) -> User | None:
        return self.get_by_id(telegram_id)

    def get_user_by(
        self,
        filter=None,
        limit: int | None = None,
        offset: int | None = None
    ) -> list[User]:
        def _get(session: Session):
            if filter is None:
                f = User.action == True
            else:
                f = filter
            query = (
                select(User)
                .filter(f)
                .order_by(User.exit_date.asc())
            )
            if limit is not None:
                query = query.limit(limit)
            if offset is not None:
                query = query.offset(offset)
            return list(session.execute(query).scalars().all())

        return self._execute_in_session(_get, commit=False)

    def get_user_by_country(
        self, country_value: int, filter: BinaryExpression | None = None
    ) -> Iterable[User]:
        def _get(session: Session):
            query = (
                select(User)
                .join(
                    ServersTable,
                    and_(
                        ServersTable.id == User.server_id,
                        ServersTable.country == country_value
                    )
                )
            )
            if filter is not None:
                query = query.filter(filter)
            return list(session.execute(query).scalars().all())

        return self._execute_in_session(_get, commit=False)

    def reduce_time_by(self, user: User, month: int) -> None:
        def _reduce(session: Session):
            session.execute(
                update(User)
                .where(User.telegram_id == user.telegram_id)
                .values(exit_date=text(f"exit_date - INTERVAL '{month} months'"))
            )

        self._execute_in_session(_reduce)

    def update_user_renewal(
        self,
        telegram_id: int,
        interval_sql: str,
        server_link: str,
        server_id: int,
        protocol: int
    ) -> None:
        def _update(session: Session):
            session.execute(
                text(
                    "UPDATE users_subscription SET exit_date="
                    "CASE WHEN exit_date > now() THEN exit_date " + interval_sql +
                    " ELSE now() " + interval_sql + " END, action=True, paid=True, "
                    "server_link=:server_link, server_id=:server_id, protocol=:protocol "
                    "WHERE telegram_id=:telegram_id"
                ),
                {
                    "server_link": server_link,
                    "server_id": server_id,
                    "protocol": protocol,
                    "telegram_id": telegram_id
                }
            )

        self._execute_in_session(_update)

    def insert_user(
        self,
        telegram_id: int,
        name: str,
        exit_date_expr: str,
        server_link: str,
        server_id: int,
        protocol: int,
        paid: bool = False
    ) -> None:
        def _insert(session: Session):
            session.execute(
                insert(User).values(
                    telegram_id=str(telegram_id),
                    name=str(name),
                    exit_date=text(exit_date_expr),
                    action=True,
                    server_link=server_link,
                    server_id=str(server_id),
                    protocol=str(protocol),
                    paid=paid
                )
            )

        self._execute_in_session(_insert)

    def update_user_extend_subscription(self, telegram_id: int, interval_sql: str) -> None:
        def _update(session: Session):
            session.execute(
                text(
                    "UPDATE users_subscription SET exit_date= exit_date " + interval_sql +
                    ", paid=True WHERE telegram_id=" + str(telegram_id)
                )
            )

        self._execute_in_session(_update)

    def update_user_deactivate(self, user_ids: set[int], commit: bool = True) -> None:
        def _update(session: Session):
            session.execute(
                update(User).where(User.telegram_id.in_(user_ids)).values(action=False)
            )

        self._execute_in_session(_update, commit=commit)

    def get_inactive_users_by_server(self) -> list:
        def _get(session: Session):
            query = select(
                func.json_agg(User.telegram_id).label('user_ids'),
                User.server_id
            ).where(User.action == False).group_by(User.server_id)
            return session.execute(query).all()

        return self._execute_in_session(_get, commit=False)

    def check_user_has_active_subscription(self, telegram_id: int) -> bool:
        def _check(session: Session):
            result = session.execute(
                text(
                    "SELECT EXISTS(SELECT 1 FROM users_subscription WHERE action = true AND telegram_id = :tid)"
                ),
                {"tid": telegram_id}
            )
            return result.scalar_one()

        return self._execute_in_session(_check, commit=False)

    def get_all_telegram_ids(self) -> list:
        def _get(session: Session):
            result = session.execute(text("SELECT telegram_id FROM users_subscription"))
            return [row[0] for row in result.fetchall()]

        return self._execute_in_session(_get, commit=False)

    def get_active_users_by_server(self, server_id: int) -> list:
        def _get(session: Session):
            result = session.execute(
                text(
                    "SELECT telegram_id, name FROM users_subscription "
                    "WHERE action = True AND server_id = :server_id"
                ),
                {"server_id": server_id}
            )
            return [{"telegram_id": row[0], "name": row[1]} for row in result]

        return self._execute_in_session(_get, commit=False)

    def update_user_server_link(self, telegram_id: int, server_link: str) -> None:
        def _update(session: Session):
            session.execute(
                text(
                    "UPDATE users_subscription SET server_link = :server_link WHERE telegram_id = :telegram_id"
                ),
                {"server_link": server_link, "telegram_id": telegram_id}
            )

        self._execute_in_session(_update)

    def update_user_server_and_link(
        self, telegram_id: int, server_link: str, server_id: int, protocol: int
    ) -> None:
        def _update(session: Session):
            session.execute(
                text(
                    "UPDATE users_subscription SET server_link = :server_link, "
                    "server_id = :server_id, protocol = :protocol WHERE telegram_id = :telegram_id"
                ),
                {
                    "server_link": server_link,
                    "server_id": server_id,
                    "protocol": protocol,
                    "telegram_id": telegram_id
                }
            )

        self._execute_in_session(_update)

    def delete_user(self, telegram_id: int) -> bool:
        return self.delete(telegram_id)


# Синглтон для обратной совместимости
user_repository = UserRepository()
