import pytest
from freezegun import freeze_time

from datetime import date, datetime
from typing import List
from app.holiday_day_count import HolidayDayCount


@pytest.fixture
def holiday_calculate(app_context):
    # cat DB おすすめID
    # 113 142 171 179 201 231 249, 75 184 242
    # holiday_base_time など必要な初期化値は適宜調整
    return HolidayDayCount(id=20)


@pytest.mark.skip
def test_get_diff_month(holiday_calculate):
    result = holiday_calculate.get_diff_month()
    # print(f"Diff month: {result}")
    assert result == 0


# @pytest.mark.skip
# @pytest.mark.freeze_time(datetime(2025, 9, 30))
def test_print_acquisition_data(holiday_calculate):
    base_day = holiday_calculate.convert_base_day(holiday_calculate.in_day)
    print(f"Base day: {base_day}")
    print(
        f"Acqisition list: {holiday_calculate.get_acquisition_list(base_day)}"
    )  # デバッグ用
    print(f"付与日 > : {holiday_calculate.print_acquisition_data()}")
    # from_list, to_list = holiday_calculate.print_acquisition_data()
    # recent_from = from_list[:-1]
    # recent_to = to_list[:-1]
    # print(f"Recent from: {recent_from}, Recent to: {recent_to}")  # デバッグ用


@pytest.mark.skip
def test_count_workdays(holiday_calculate):
    result = holiday_calculate.count_workdays()
    print(f"Count work list: {result}")


@pytest.mark.skip
def test_count_workday_half_year(holiday_calculate):
    test_workdays = holiday_calculate.count_workdays()
    result = holiday_calculate.count_workday_half_year(test_workdays[0])
    print(f"First work count: {result}")


# @pytest.mark.skip
def test_acqire_holidays_dict_mock(monkeypatch, holiday_calculate):
    work_half_count = 180
    monkeypatch.setattr(
        holiday_calculate,
        "count_workday_half_year",
        lambda: work_half_count,
    )
    # 例: 直近2期間分の勤務日数が180
    acqisition_date_dict = holiday_calculate.acquire_holidays_dict(180)
    print(f"{acqisition_date_dict}")
    # assert list(acqisition_date_dict.values())[-3] == 8


@pytest.mark.skip
def test_acquire_holidays_dict(holiday_calculate):
    work_count_list = holiday_calculate.count_workdays()
    acqisition_data_list: List[dict[date, int]] = [
        holiday_calculate.acquire_holidays_dict(wc) for wc in work_count_list
    ]
    print(acqisition_data_list)


@pytest.mark.skip
# @pytest.mark.freeze_time(datetime(2025, 9, 30))
def test_count_recent_workdays(holiday_calculate):
    test_workdays = holiday_calculate.count_recent_workdays()
    test_acqisition = holiday_calculate.select_next_holiday(test_workdays)
    print(f"Work count and next holiday: {test_workdays}, {test_acqisition}")
    assert test_acqisition == 8


# @pytest.mark.skip
# def test_acquire_holidays_dict(holiday_calculate):
#     q1_result = holiday_calculate.acquire_holidays_dict(50)
#     q2_result = holiday_calculate.acquire_holidays_dict(180)
#     q3_result = holiday_calculate.acquire_holidays_dict(220)
#     print(
#         f"Q1 Result: {q1_result}, Q2 Result: {q2_result}, Q3 Result: {q3_result}"
#     )  # デバッグ用


# @pytest.mark.skip
# @pytest.mark.freeze_time(datetime(2025, 9, 30))
def test_get_effective_holidays(monkeypatch, holiday_calculate):
    work_half_count = 220
    # 例: 直近2期間分の勤務日数が180日、220日だった場合
    work_counts = [180, 220, 200]

    # count_workdayをモック
    # TypeError: <lambda>() takes 0 positional arguments but 1 was given
    # https://stackoverflow.com/questions/54641750/typeerror-lambda-takes-0-positional-arguments-but-1-was-given-due-to-monkey
    monkeypatch.setattr(
        holiday_calculate, "count_workday_half_year", lambda x: work_half_count
    )
    monkeypatch.setattr(holiday_calculate, "count_workdays", lambda: work_counts)

    # 期待される付与区分・付与日数はacquisition_type.pyのロジックに合わせて決定
    # 例: 30→30*12/2, 180→B区分, 220→A区分
    # ここでは例として単純に合計日数を計算
    result = holiday_calculate.get_effective_holidays()
    print(f"Test add holiday list: {result}")
    # 期待値の詳細なassert例（acquisition_type.pyの内容に合わせて調整）
    # assert result == (B区分の2年目日数 + A区分の3年目日数) * 8.0


# 出勤日数カウント(半年未満)
@pytest.mark.skip
def test_count_workday_half(holiday_calculate):
    test_count = holiday_calculate.count_workday_half_year()
    print(f"出勤日数カウント: {test_count}")
