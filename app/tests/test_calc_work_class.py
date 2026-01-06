import pytest
from datetime import timedelta


from app.calc_work_classes3 import CalcTimeFactory


@pytest.fixture
def calc_time_instance():
    calc_time_factory = CalcTimeFactory()
    calc_time_instance = calc_time_factory.get_instance(20)
    return calc_time_instance


attendance_test_data = [
    # c_work_time, c_holiday_time, sh_starttime, sh_endtime, notifications, sh_overtime, sh_holiday
    (8.0, 8.0, "09:00", "18:30", ("", ""), "1", "0"),  # Regular day
    (8.0, 8.0, "09:00", "13:30", ("", "4"), "0", "0"),  # Half-day off and overtime
    # (8.0, 8.0, "00:00", "00:00", ("8", ""), "0", "0"),  # Full-day off
    (8.0, 8.0, "09:00", "17:30", ("", ""), "0", "0"),  # Irregular work time
    (7.0, 7.5, "09:00", "13:00", ("", "16"), "0", "0"),  # Half-day off (7h work)
    (8.0, 8.0, "13:00", "18:00", ("6", ""), "1", "0"),  # Half-day business trip
    (
        8.0,
        8.0,
        "09:00",
        "13:00",
        ("10", "4"),
        "0",
        "0",
    ),  # Half-day business trip and half-day off
]


@pytest.fixture(params=attendance_test_data)
def calc_time_set_data(
    request,
    calc_time_instance,
):
    calc_time_instance.set_data(
        c_work_time=request.param[0],
        c_holiday_time=request.param[1],
        sh_starttime=request.param[2],
        sh_endtime=request.param[3],
        notifications=request.param[4],
        sh_overtime=request.param[5],
        sh_holiday=request.param[6],
    )
    # return request.param
    return calc_time_instance


@pytest.mark.skip
def test_print_instance_fixture(calc_time_set_data):
    print(calc_time_set_data)


def test_provide_half_rest(calc_time_set_data):
    result = calc_time_set_data._provide_half_notify()
    print(f"Calculated provide time: {result}")


# @pytest.mark.skip
def test_check_over_work(calc_time_set_data):
    result = calc_time_set_data.check_over_work()
    print(f"Calculated actual work time: {result}")


@pytest.mark.skip
def test_get_over_time(calc_time_set_data):
    if calc_time_set_data.sh_overtime == "1":
        result = calc_time_set_data.get_over_time()
        print(f"Calculated over work time: {result}")


def test_get_real_time(calc_time_set_data):
    result = calc_time_set_data.get_real_time()
    print(f"Calculated real work time: {result}")
