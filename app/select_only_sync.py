import os
from typing import Optional, List

from sqlalchemy import create_engine, and_
from sqlalchemy.orm import scoped_session, sessionmaker, Query

from app.models import TableOfCount


def get_panda_url(sql_module: str = "pymysql"):

    return "mysql+{mysql_module}://{user}:{password}@{host}:{port}/{db_name}?charset=utf8mb4".format(
        **{
            "mysql_module": sql_module,
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "host": os.getenv("DB_HOST"),
            "port": os.getenv("DB_PORT"),
            "db_name": os.getenv("DB_NAME"),
            # "host": "127.0.0.1",
            # "port": "3307",
            # "db_name": "panda",
        }
    )


""" 一時的なpandaからのSelect """

read_engine = create_engine(url=get_panda_url("pymysql"))
# セッションファクトリーを作成
read_session = scoped_session(sessionmaker(bind=read_engine))


def get_sync_record(primary_key: str) -> Optional[TableOfCount]:
    return read_session.get(TableOfCount, primary_key)


# def get_count_table(
#     year_and_month: str, base_day: str, staff_id: int, contract_code: int
# ) -> Query[TableOfCount]:
#     making_id = f"{year_and_month}-{base_day}-{staff_id}-{contract_code}"
#     return read_session.get(TableOfCount, making_id)


def get_count_table(
    staff_id: int, contract_code: int, year_and_month: str
) -> TableOfCount:
    return (
        read_session.query(TableOfCount)
        .filter(
            and_(
                TableOfCount.STAFFID == staff_id,
                TableOfCount.CONTRACT_CODE == contract_code,
                TableOfCount.YEAR_MONTH == year_and_month,
            )
        )
        .first()
    )
