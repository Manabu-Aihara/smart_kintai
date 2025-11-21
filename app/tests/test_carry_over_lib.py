import pytest
from pytest_mock import MockFixture
from typing import OrderedDict
from datetime import date


from app.holiday_day_count import HolidayDayCount
from app.carry_over_lib import (
    calc_leave_sum_days,
    get_alert_target_dict,
)

# 仮のAPIデータ例
mock_api_data_20 = [
    {
        "staff_id": 20,
        "contract_work_hours": 8.0,
        "contract_vacation_hours": 8.0,
        "leave_full": 12,
        "leave_half": 2,
        "hourly_leave": 10,
        "half_hour_leave": 3,
    }
]
mock_api_data_31 = [
    {
        "staff_id": 31,
        "contract_work_hours": 6.0,
        "contract_vacation_hours": 6.0,
        "leave_full": 5,
        "leave_half": 4,
        "hourly_leave": 2,
        "half_hour_leave": 2,
    }
]
mock_api_data_194 = [
    {
        "staff_id": 194,
        "contract_work_hours": 7.0,
        "contract_vacation_hours": 7.0,
        "leave_full": 5,
        "leave_half": 3,
        "hourly_leave": 3,
        "half_hour_leave": 3,
    },
    {
        "staff_id": 194,
        "contract_work_hours": 7.5,
        "contract_vacation_hours": 7.5,
        "leave_full": 1,
        "leave_half": 2,
        "hourly_leave": 3,
        "half_hour_leave": 0,
    },
]
mock_api_data_256 = [
    {
        "staff_id": 256,
        "contract_work_hours": 7.0,
        "contract_vacation_hours": 7.0,
        "leave_full": 2,
        "leave_half": 0,
        "hourly_leave": 2,
        "half_hour_leave": 0,
    }
]


@pytest.fixture
def holiday_obj(app_context):
    return HolidayDayCount(id=256)


@pytest.fixture(name="holidays_under")
def get_grant_holidays_under(
    holiday_obj, mocker: MockFixture
) -> OrderedDict[date, int]:
    work_half_count = 220
    work_counts = [180, 220]

    # count_workdayをモック
    mock_half_count = mocker.patch.object(
        HolidayDayCount, "count_workday_half_year", return_value=work_half_count
    )
    mocker.patch.object(HolidayDayCount, "count_workdays", return_value=work_counts)

    result = holiday_obj.get_effective_holidays()
    assert mock_half_count.call_count == 1
    return result


@pytest.fixture(name="holidays_over")
def get_grant_holidays_over(holiday_obj, mocker: MockFixture) -> OrderedDict[date, int]:
    work_counts = [180, 220, 220]

    # count_workdayをモック
    mocker.patch.object(HolidayDayCount, "count_workdays", return_value=work_counts)

    return holiday_obj.get_effective_holidays()


@pytest.mark.skip
def test_app_data_mock(holidays_under, holidays_over):
    print(f"Under holidays: {holidays_under}")
    print(f"Over holidays: {holidays_over}")


@pytest.mark.skip
def test_calc_leave_sum_days(app_context):
    for data in mock_api_data_194:
        result = calc_leave_sum_days(data)
        print(f"Rsult times={result}")


# @pytest.mark.skip
def test_alert_target_dict_under(holidays_under, mocker: MockFixture):
    print(f"Grant holidays: {holidays_under}")
    mock_effective_holidays = mocker.patch.object(
        HolidayDayCount, "get_effective_holidays", return_value=holidays_under
    )
    test_notification = get_alert_target_dict(mock_api_data_256)
    print(f"Test notification: {test_notification}")
    assert mock_effective_holidays.called


@pytest.mark.skip
def test_alert_target_dict_over(holidays_over, mocker: MockFixture):
    print(f"Grant holidays: {holidays_over}")
    mock_effective_holidays = mocker.patch.object(
        HolidayDayCount, "get_effective_holidays", return_value=holidays_over
    )
    test_notification = get_alert_target_dict(mock_api_data_20)
    print(f"Test notification: {test_notification}")
    assert mock_effective_holidays.called
