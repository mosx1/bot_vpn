"""
Репозиторий операций приглашений (обновление invited, balance).
"""
from sqlalchemy.orm import Session
from sqlalchemy import text

from database.repositories.base_repository import BaseRepository
from database.models import User


class InviteRepository(BaseRepository[User]):
    """Репозиторий операций приглашений (работа с полями invited, balance в User)."""

    @property
    def model(self) -> type[User]:
        return User

    @property
    def pk_column(self):
        return User.telegram_id

    def write_invited(self, user_id: str, invited_user_id: str) -> None:
        def _write(session: Session):
            session.execute(
                text(
                    "UPDATE users_subscription SET invited = :invited "
                    "WHERE telegram_id = :user_id"
                ),
                {"invited": invited_user_id, "user_id": user_id}
            )

        self._execute_in_session(_write)

    def increment_balance(
        self, user_id: str, month: int | None = None, summ: int | None = None
    ) -> None:
        if month is not None and summ is None:
            from configparser import ConfigParser
            conf = ConfigParser()
            conf.read('config.ini')
            summ = conf['Price'].getint('RUB') * month

        if summ is None:
            return

        def _increment(session: Session):
            session.execute(
                text(
                    "UPDATE users_subscription SET balance = balance + :summ "
                    "WHERE telegram_id = (SELECT invited FROM users_subscription WHERE telegram_id = :user_id)"
                ),
                {"summ": summ, "user_id": user_id}
            )

        self._execute_in_session(_increment)

    def reset_to_zero_balance(self, user_id: str) -> None:
        def _reset(session: Session):
            session.execute(
                text("UPDATE users_subscription SET balance = 0 WHERE telegram_id = :user_id"),
                {"user_id": user_id}
            )

        self._execute_in_session(_reset)


# Синглтон
invite_repository = InviteRepository()
