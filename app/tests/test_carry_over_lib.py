from datetime import date
from app.carry_over_lib import calcurate_carry_times

# 仮のAPIデータ例
mock_api_data = [
    {
        "staff_id": 20,
        "contract_work_hours": 8.0,
        "contract_vacation_hours": 8.0,
        "workday_count": 220,
        "annual_leave_full": 12,
        "annual_leave_half": 2,
        "hourly_leave": 10.0,
        "half_hour_leave": 3.0,
        # "in_day": date(2017, 4, 1),
    },
    {
        "staff_id": 201,
        "contract_work_hours": 6.0,
        "contract_vacation_hours": 6.0,
        "workday_count": 180,
        "annual_leave_full": 10,
        "annual_leave_half": 1,
        "hourly_leave": 7,
        "half_hour_leave": 2,
        # "in_day": date(2018, 4, 1),
    },
]


def test_calcurate_carry_times(app_context):
    for member in mock_api_data:
        result = calcurate_carry_times(member)
        print(f"staff_id={member['staff_id']} carry_over={result}")
        assert isinstance(result, float)
