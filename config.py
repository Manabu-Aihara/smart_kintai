import os

"""
    2023/8/8追加
    .envファイル参照
    """
from dotenv import load_dotenv

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    DEBUG = True

    SQLALCHEMY_DATABASE_URI = (
        "mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}?charset=utf8".format(
            **{
                "user": os.getenv("DB_USER"),
                "password": os.getenv("DB_PASSWORD"),
                "host": os.getenv("DB_HOST"),
                "port": os.getenv("DB_PORT"),
                "db_name": os.getenv("DB_NAME"),
            }
        )
    )
    SECRET_KEY = os.environ.get("SECRET_KEY") or "you-will-never-guess"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
