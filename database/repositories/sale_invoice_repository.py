"""
Репозиторий счетов на оплату в процессе.
"""
from sqlalchemy.orm import Session
from sqlalchemy import select, insert, delete, text, func

from database.repositories.base_repository import BaseRepository
from database.models import SaleInvoicesInProgress


class SaleInvoiceRepository(BaseRepository[SaleInvoicesInProgress]):
    @property
    def model(self) -> type[SaleInvoicesInProgress]:
        return SaleInvoicesInProgress

    @property
    def pk_column(self):
        return SaleInvoicesInProgress.id

    def add_sale_invoice(
        self,
        label: str,
        user_id: int,
        server_id: int,
        month_count: int,
        chat_id: int,
        message_id: int
    ) -> None:
        def _add(session: Session):
            session.execute(
                insert(SaleInvoicesInProgress).values(
                    telegram_id=user_id,
                    label=label,
                    server_id=server_id,
                    month_count=month_count,
                    chat_id=chat_id,
                    message_id=message_id
                )
            )

        self._execute_in_session(_add)

    def get_invoices_with_expiry(self) -> list:
        def _get(session: Session):
            query = select(
                SaleInvoicesInProgress,
                (SaleInvoicesInProgress.create_date + text("INTERVAL '1 hour'")).label("stop_date_time"),
                func.now().label("current_date_time")
            )
            result = session.execute(query)
            return result.fetchall()

        return self._execute_in_session(_get, commit=False)

    def delete_invoice(self, invoice_id: int) -> bool:
        return self.delete(invoice_id)


# Синглтон
sale_invoice_repository = SaleInvoiceRepository()
