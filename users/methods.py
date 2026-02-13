"""
Фасад над репозиторием пользователей. Сохраняет обратную совместимость.
"""
from typing import Iterable

from database import (
    User,
    get_user_by_id,
    get_user_by,
    get_user_by_country as _get_user_by_country,
    add_subscription_for_user,
    reduce_time_by,
)

from servers.server_list import Country


def get_user_by_country(country: Country, filter=None) -> Iterable[User]:
    """Получить пользователей по стране."""
    return _get_user_by_country(country.value, filter)
