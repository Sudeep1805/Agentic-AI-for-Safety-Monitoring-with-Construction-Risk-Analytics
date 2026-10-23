from sqlalchemy import URL, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import Settings


class Base(DeclarativeBase):
    pass


def make_engine(settings: Settings):
    # URL.create handles passwords containing @, :, / and other special characters.
    url = URL.create(
        "mysql+pymysql",
        username=settings.mysql_user,
        password=settings.mysql_password.get_secret_value(),
        host=settings.mysql_host,
        port=settings.mysql_port,
        database=settings.mysql_database,
        query={"charset": "utf8mb4"},
    )
    return create_engine(
        url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 3, "read_timeout": 5, "write_timeout": 5},
    )


def make_session_factory(engine):
    return sessionmaker(bind=engine, expire_on_commit=False)

