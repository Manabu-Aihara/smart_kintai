import pytest
from pytest_mock import MockFixture
from app.carry_over_lib import (
    calc_leave_sum_days,
    calculate_carry_over,
    calculate_carry_over_all,
)

# 仮のAPIデータ例
mock_api_data = [
    {
        "staff_id": 20,
        "contract_work_hours": 8.0,
        "contract_vacation_hours": 8.0,
        # "workday_count": 440,
        "leave_full": 12,
        "leave_half": 2,
        "hourly_leave": 10,
        "half_hour_leave": 3,
    },
    {
        "staff_id": 194,
        "contract_work_hours": 7.0,
        "contract_vacation_hours": 7.0,
        # "workday_count": 300,
        "leave_full": 5,
        "leave_half": 3,
        "hourly_leave": 3,
        "half_hour_leave": 3,
    },
    {
        "staff_id": 194,
        "contract_work_hours": 7.5,
        "contract_vacation_hours": 7.5,
        # "workday_count": 60,
        "leave_full": 1,
        "leave_half": 2,
        "hourly_leave": 3,
        "half_hour_leave": 0,
    },
]


def test_calc_leave_sum_days(app_context):
    for member in mock_api_data:
        result = calc_leave_sum_days(member)
        print(f"Rsult times={result}")


def test_calculate_carry_over(mocker: MockFixture, app_context):
    mock_workday_count = mocker.patch(
        "app.carry_over_lib.HolidayCalculate.get_valid_holidays",
        return_value=[8, 9],
    )
    result_carry = calculate_carry_over(mock_api_data, 194)
    print(f"Carry over for staff is {result_carry}")
    assert result_carry == 6.5

    # 17-5-3/2-1=9.5
    # 9.5-1-2/2-1=6.5

    assert mock_workday_count.called
    # if member["staff_id"] == 20:
    #     result = calcurate_carry_over(member, 20)
    #     print(f"Carry over for staff is {result}")
    #     assert result == 23  # 期待値は38-12-2/2-2=23


def test_calculate_carry_over_all(mocker: MockFixture, app_context):
    mock_workday_count = mocker.patch(
        "app.carry_over_lib.HolidayCalculate.get_valid_holidays",
        return_value=[18, 20],  # 20
        # return_value=[8, 9], # 194
    )
    result_carry_all = calculate_carry_over_all(mock_api_data)
    print(f"Carry over for staff is {result_carry_all}")
    assert result_carry_all == {20: 23, 194: 6.5}

    assert mock_workday_count.called
