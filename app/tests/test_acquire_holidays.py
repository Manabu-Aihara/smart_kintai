import pytest
from unittest.mock import MagicMock, patch

from app.database_base import session
from app.models_aprv import PaidHolidayLog
from app.acquisition_holidays_lib import acquire_holidays_from_now


def get_workdays():
    return [220, 220, 160, 220, 180]


@pytest.fixture(name="workdays")
def count_workdays_dummy():
    return get_workdays()


@pytest.fixture
def add_acquisition_params(workdays):
    return {"workdays": workdays}


def test_print_param_fixture(add_acquisition_params):
    print(f"ダミーの勤務日数: {add_acquisition_params.get('workdays')}")


def test_aqcuire_holidays_from_now(mocker, workdays):
    from app.acquisition_holidays_lib import acquire_holidays_from_now

    # acquire_holidays_from_now関数をモック化
    workdays_mock = mocker.patch(
        "app.acquisition_holidays_lib.HolidayDayCount.count_recent_workdays",
        side_effect=workdays,
    )
    # テスト対象の関数を実行
    from_now_on_holidays = acquire_holidays_from_now()
    print(f"Test debug: {from_now_on_holidays}日")

    assert workdays_mock.call_count == 5


@pytest.mark.skip
def add_acquisition_data() -> None:
    try:
        holiday_info_dict = acquire_holidays_from_now()
        for concerned_staff, holiday_info_dict in holiday_info_dict.items():
            from_now_on_holidays: int = holiday_info_dict.get("from_now_on_grant", 0)
            print(f"Debug: {concerned_staff} → {from_now_on_holidays}日")
            add_data = PaidHolidayLog(
                concerned_staff, from_now_on_holidays, None, None, None, None
            )
            session.add(add_data)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# add_acquisition_data 関数が依存している session オブジェクトをモック化
@pytest.fixture
def mock_session():
    # sessionオブジェクトをモック化
    mock_session_instance = MagicMock()

    # sessionオブジェクト全体をモック化
    with patch("app.acquisition_holidays_lib.session", mock_session_instance):
        yield mock_session_instance
        # テストが終わったらモックを解放
        mock_session_instance.close()


def test_add_acquisition_db_commits_data(mock_session):
    # from app.acquisition_holidays_lib import add_acquisition_data

    # テスト対象の関数を実行
    add_acquisition_data()

    # 検証1: session.commit() が1回だけ呼び出されたことを確認
    mock_session.commit.assert_called_once()

    # 検証2: session.rollback() が呼び出されていないことを確認
    mock_session.rollback.assert_not_called()


def test_add_acquisition_db_rolls_back_on_error(mock_session):
    # from app.acquisition_holidays_lib import add_acquisition_data

    # session.commit() の実行時に例外を発生させるように設定
    mock_session.commit.side_effect = Exception("Database error")

    # 例外が発生することを確認
    with pytest.raises(Exception):
        add_acquisition_data()

    # 検証: session.rollback() が1回だけ呼び出されたことを確認
    mock_session.rollback.assert_called_once()

    # 検証: session.commit() が1回だけ呼び出されたことを確認（例外発生前）
    mock_session.commit.assert_called_once()
