import pytest

import sys

# sys.path.append(os.path.abspath(".."))
import pathlib
from os.path import join

from dotenv import load_dotenv


packagedir = pathlib.Path(__file__).resolve().parent.parent.parent
print(packagedir)
sys.path.append(str(packagedir))

dotenv_path = join(str(packagedir), ".env")
load_dotenv(dotenv_path)

from app import db, app


@pytest.fixture(scope="session")
def app_context():
    """Flaskアプリケーションコンテキストを有効化"""
    with app.app_context():
        db.create_all()
        yield
        # db.session.remove()
        # db.drop_all()


# from app.database_base import engine, Session


# @pytest.fixture(scope="function")
# def request_context(app_context):
#     """リクエストコンテキストも有効化"""
#     with app.test_request_context():
#         yield


# @pytest.fixture(scope="function")
# def db_session():
#     """各テストごとに新しいDBセッションを提供し、テスト後ロールバックするfixture"""
#     connection = engine.connect()
#     transaction = connection.begin()
#     session = Session(bind=connection)

#     yield session

#     session.close()
#     transaction.rollback()
#     connection.close()


# def test_something(db_session):
#     # db_sessionでDBアクセス
#     result = db_session.execute("SELECT 1")
#     assert result.scalar() == 1
