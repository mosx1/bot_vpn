from connect import engine

from sqlalchemy import Column,Numeric, BIGINT, TEXT, TIMESTAMP, BOOLEAN, String, ForeignKeyConstraint, INTEGER, VARCHAR, TIME, SMALLINT,func, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB


Base = declarative_base()

class User(Base):

    __tablename__: str = 'users_subscription'

    telegram_id: Column = Column(BIGINT, primary_key=True)
    name: Column = Column(TEXT, nullable=True)
    exit_date: Column = Column(TIMESTAMP, nullable=False)
    action: Column = Column(BOOLEAN, nullable=False)
    server_link: Column = Column(TEXT, nullable=False)
    server_id: Column = Column(BIGINT, nullable=False)
    server_desired: Column = Column(String, nullable=True)
    paid: Column = Column(BOOLEAN, nullable=False)
    protocol: Column = Column(BIGINT, nullable=False)
    statistic: Column = Column(TEXT, nullable=True)
    balance: Column = Column(Numeric, nullable=True)
    invited: Column = Column(BIGINT, nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(['invited'], ['users_subscription.telegram_id']),
        ForeignKeyConstraint(['server_id'], ['servers.id'])
    )


class ServersTable(Base):

    __tablename__: str = 'servers'

    id: Column = Column(INTEGER, primary_key=True)
    links: Column = Column(TEXT, nullable=False)
    country: Column = Column(INTEGER, nullable=False)
    name: Column = Column(TEXT, nullable=False)
    speed: Column[int] = Column(INTEGER)


class CountryTable(Base):

    __tablename__: str = 'country'

    id: Column = Column(INTEGER, primary_key=True)
    name: Column = Column(VARCHAR(64), nullable=False)


class SecurityHashs(Base):

    __tablename__: str = 'securityhashs'

    hash: Column[str] = Column(TEXT, primary_key=True)
    data: Column = Column(TIME(timezone=True), nullable=False, default=func.now())


class GiftCodes(Base):

    __tablename__: str = 'gift_codes'

    code: Column[str] = Column(TEXT, primary_key=True)
    month: Column[int] = Column(SMALLINT, nullable=False)


class UserToSubscription(Base):

    __tablename__: str = 'user_to_subscription'

    telegram_id: Column = Column(BIGINT, nullable=False)
    server_link: Column = Column(TEXT, primary_key=True)
    server_id: Column = Column(BIGINT, nullable=False)

    __table_agrs___ = (
        ForeignKeyConstraint(['telegram_id'], ['users_subscription.telegram_id']),
        ForeignKeyConstraint(['server_id'], ['servers.id'])
    )

class ConfigsServers(Base):

    __tablename__: str = 'configs_servers'

    id = Column(BIGINT, primary_key=True)
    server_id = Column(BIGINT, nullable=False)
    config = Column(JSONB)

    __table_agrs___ = (
        ForeignKeyConstraint(['server_id'], ['servers.id'])
    )
    

class SaleInvoicesInProgress(Base):
    
    __tablename__: str = 'sale_invoices_in_progress'

    id: Column = Column(BIGINT, primary_key=True)
    telegram_id: Column = Column(BIGINT, nullable=False)
    label: Column = Column(TEXT, nullable=False)
    server_id: Column = Column(BIGINT, nullable=False)
    month_count: Column = Column(SMALLINT, nullable=False)
    message_id: Column = Column(BIGINT, nullable=False)
    chat_id: Column = Column(BIGINT, nullable=False)
    create_date: Column = Column(TIMESTAMP, nullable=False, server_default=func.now())

    __table_agrs___ = (
        ForeignKeyConstraint(['telegram_id'], ['users_subscription.telegram_id']),
        ForeignKeyConstraint(['server_id'], ['servers.id'])
    )

Base.metadata.create_all(engine)