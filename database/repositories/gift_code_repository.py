"""
Репозиторий подарочных кодов.
"""
from sqlalchemy.orm import Session
from sqlalchemy import text

from database.repositories.base_repository import BaseRepository
from database.models import GiftCodes


class GiftCodeRepository(BaseRepository[GiftCodes]):
    @property
    def model(self) -> type[GiftCodes]:
        return GiftCodes

    @property
    def pk_column(self):
        return GiftCodes.code

    def gen_gift_code(self, month: int) -> str:
        def _gen(session: Session):
            result = session.execute(
                text(
                    "INSERT INTO gift_codes (code, month) VALUES (md5(random()::text), :month) RETURNING code"
                ),
                {"month": month}
            )
            return result.scalar_one()

        return self._execute_in_session(_gen)

    def check_and_consume_gift_code(self, code: str) -> int | None:
        def _check(session: Session):
            result = session.execute(
                text("SELECT month FROM gift_codes WHERE code = :code"),
                {"code": code}
            )
            gift_data = result.fetchone()
            if gift_data:
                month = gift_data[0]
                if month:
                    session.execute(
                        text("DELETE FROM gift_codes WHERE code = :code"),
                        {"code": code}
                    )
                    return month
            return None

        return self._execute_in_session(_check)


# Синглтон
gift_code_repository = GiftCodeRepository()
