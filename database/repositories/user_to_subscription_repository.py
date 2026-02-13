"""
Репозиторий связи пользователь-подписка.
"""
from sqlalchemy import insert

from database.repositories.base_repository import BaseRepository
from database.models import UserToSubscription


class UserToSubscriptionRepository(BaseRepository[UserToSubscription]):
    @property
    def model(self) -> type[UserToSubscription]:
        return UserToSubscription

    @property
    def pk_column(self):
        return UserToSubscription.server_link

    def add_subscription_for_user(self, telegram_id: int, server_link: str, server_id: str) -> None:
        def _add(session):
            session.execute(
                insert(UserToSubscription).values(
                    telegram_id=telegram_id,
                    server_link=server_link,
                    server_id=server_id
                )
            )

        self._execute_in_session(_add)


# Синглтон
user_to_subscription_repository = UserToSubscriptionRepository()
