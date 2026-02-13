"""
Репозиторий серверов и стран.
"""
from typing import Tuple

from configparser import ConfigParser

from sqlalchemy.orm import Session
from sqlalchemy import Row, Sequence, select, func, and_, text, update
from sqlalchemy.sql.elements import BinaryExpression

from database.repositories.base_repository import BaseRepository
from database.models import ServersTable, CountryTable, User


class ServerRepository(BaseRepository[ServersTable]):
    @property
    def model(self) -> type[ServersTable]:
        return ServersTable

    @property
    def pk_column(self):
        return ServersTable.id

    def get_server_list(self, filter: BinaryExpression | None = None) -> list[ServersTable]:
        def _get(session: Session):
            query = select(ServersTable)
            if filter:
                query = query.filter(filter)
            return list(session.execute(query).scalars().all())

        return self._execute_in_session(_get, commit=False)

    def get_country_list(self, filter: BinaryExpression | None = None) -> list[CountryTable]:
        def _get(session: Session):
            query = select(CountryTable)
            if filter:
                query = query.filter(filter)
            return list(session.execute(query).scalars().all())

        return self._execute_in_session(_get, commit=False)

    def get_server_name_by_id(self, server_id: int) -> str:
        server = self.get_by_id(server_id)
        return server.name if server else "Неизвестное наименование сервера"

    def get_server_url_by_id(self, server_id: int) -> str:
        server = self.get_by_id(server_id)
        return server.links if server else ""

    def get_very_free_server(
        self,
        country_value: int | None = None,
        exclude_server_id: int | None = None
    ) -> int:
        conf = ConfigParser()
        conf.read('config.ini')
        coefficient_load = conf['BaseConfig'].getfloat('coefficient_load_servers')

        def _get(session: Session):
            query = (
                select(
                    (func.count() / coefficient_load / ServersTable.speed).label('count'),
                    ServersTable.id
                )
                .select_from(ServersTable)
                .join(
                    User,
                    and_(
                        User.server_id == ServersTable.id,
                        User.action == True
                    ),
                    isouter=True
                )
                .filter(ServersTable.answers == True)
            )
            if country_value is not None:
                query = query.filter(ServersTable.country == country_value)
            if exclude_server_id is not None:
                query = query.filter(ServersTable.id != exclude_server_id)
            query = query.group_by(ServersTable.id).order_by(text('count ASC')).limit(1)
            result = session.execute(query).one()
            return result.id

        return self._execute_in_session(_get, commit=False)

    def get_info_all_servers(self) -> Row[Tuple]:
        def _get(session: Session):
            query = select(
                func.count().label("count"),
                func.count().filter(User.paid == True).label("count_pay")
            ).filter(User.action == True)
            return session.execute(query).one()

        return self._execute_in_session(_get, commit=False)

    def get_info_servers(self) -> Sequence[Row[Tuple]]:
        conf = ConfigParser()
        conf.read('config.ini')
        coefficient_load = conf['BaseConfig'].getfloat('coefficient_load_servers')

        def _get(session: Session):
            query = (
                select(
                    ServersTable.name.label("name"),
                    ServersTable.answers,
                    func.count().label("count"),
                    func.count().filter(User.paid == True).label("count_pay"),
                    (func.count() / coefficient_load / ServersTable.speed * 100).label('load')
                )
                .join(User, ServersTable.id == User.server_id)
                .filter(User.action == True)
                .group_by(ServersTable.name, ServersTable.speed, ServersTable.answers)
            ).order_by(text('count_pay DESC'))
            return session.execute(query).all()

        return self._execute_in_session(_get, commit=False)

    def update_answers_servers(self, server_id: int, answers: bool) -> None:
        self.update(server_id, answers=answers)


# Синглтон
server_repository = ServerRepository()
