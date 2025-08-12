import pytest
from unittest.mock import MagicMock, patch

from app.acquisition_holidays_lib import get_concerned_members, add_acquisition_data


# def get_concerned_staff_list():
#     # モックデータを返す
#     return [3, 20, 50, 150, 201]


def get_workdays():
    return [220, 220, 160, 220, 180]


@pytest.fixture(name="members")
def concerned_members_dummy(db_session):
    return get_concerned_members()


@pytest.fixture(name="workdays")
def count_workdays_dummy():
    return get_workdays()


@pytest.fixture
def add_acquisition_params(members, workdays):
    return {"members": members, "workdays": workdays}


def test_print_param_fixture(add_acquisition_params):
    print(
        f"対象ID: {add_acquisition_params.get('members')}: "
        f"ダミーの勤務日数: {add_acquisition_params.get('workdays')}"
    )


def test_aqcuire_holidays_from_now(mocker, members, workdays):
    from app.acquisition_holidays_lib import acquire_holidays_from_now

    # acquire_holidays_from_now関数をモック化
    workdays_mock = mocker.patch(
        "app.acquisition_holidays_lib.HolidayDayCount.count_recent_workdays",
        side_effect=workdays,
    )
    # テスト対象の関数を実行
    for member in members:
        from_now_on_holidays = acquire_holidays_from_now(member)
        print(f"Test debug: {member} → {from_now_on_holidays}日")

    assert workdays_mock.call_count == 5


# add_acquisition_data 関数が依存している session オブジェクトをモック化
@pytest.fixture
def mock_session(mocker, members):
    # sessionオブジェクトをモック化
    mock_session_instance = MagicMock()

    # sessionオブジェクト全体をモック化
    with patch("app.acquisition_holidays_lib.session", mock_session_instance):
        # member_count = mocker.patch(
        #     "app.acquisition_holidays_lib.get_concerned_members",
        #     return_value=members,
        # )
        yield mock_session_instance
        # テストが終わったらモックを解放
        mock_session_instance.close()

    # assert member_count.called_once


def test_add_acquisition_db_commits_data(mock_session, mocker, members):
    # こっちは失敗、実装でもテストでも、DBにアクセスしてしるから
    # member_count = mocker.patch(
    #     "app.acquisition_holidays_lib.get_concerned_members",
    #     side_effect=members,  # モックデータを返す
    # )

    # acquire_holidays_from_now関数をモック化（単純に値を返すだけ）
    # mocker.patch(
    #     "app.acquisition_holidays_lib.acquire_holidays_from_now",
    #     return_value=20,
    # )

    # テスト対象の関数を実行
    add_acquisition_data()

    # 検証1: session.commit() が1回だけ呼び出されたことを確認
    mock_session.commit.assert_called_once()

    # 検証2: session.rollback() が呼び出されていないことを確認
    mock_session.rollback.assert_not_called()

    # assert (
    #     member_count.add.call_count == 5
    # )  # 5人のスタッフに対してデータが追加されることを確認


def test_add_acquisition_db_rolls_back_on_error(mock_session, mocker, members):
    # こっちは失敗、実装でもテストでも、DBにアクセスしてしるから
    # member_count = mocker.patch(
    #     "app.acquisition_holidays_lib.get_concerned_members",
    #     side_effect=members,  # モックデータを返す
    # )

    # acquire_holidays_from_now関数をモック化（単純に値を返すだけ）
    # mocker.patch(
    #     "app.acquisition_holidays_lib.acquire_holidays_from_now",
    #     return_value=20,
    # )

    # session.commit() の実行時に例外を発生させるように設定
    mock_session.commit.side_effect = Exception("Database error")

    # 例外が発生することを確認
    with pytest.raises(Exception):
        add_acquisition_data()

    # 検証: session.rollback() が1回だけ呼び出されたことを確認
    mock_session.rollback.assert_called_once()

    # 検証: session.commit() が1回だけ呼び出されたことを確認（例外発生前）
    mock_session.commit.assert_called_once()

    # assert (
    #     member_count.add.call_count == 5
    # )  # 5人のスタッフに対してデータが追加されることを確認
