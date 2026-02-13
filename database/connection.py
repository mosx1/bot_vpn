"""
Подключение к базе данных PostgreSQL через SQLAlchemy Engine.
"""
from configparser import ConfigParser
from urllib.parse import quote_plus

from sqlalchemy import Engine, create_engine

conf = ConfigParser()
conf.read('config.ini')

postgres = conf['Postgres']
dbname = postgres.get('dbname')
user = postgres.get('user')
password = postgres.get('password')
host = postgres.get('host')

url = f"postgresql+psycopg2://{quote_plus(user)}:{quote_plus(password)}@{host}/{dbname}"
engine: Engine = create_engine(url, echo=False)
