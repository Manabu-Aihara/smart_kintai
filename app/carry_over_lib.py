import math
from datetime import date, datetime
from typing import Tuple, Dict
from collections import defaultdict

from .holiday_day_count import HolidayDayCount


def config_from_to_holiday() -> Tuple[date, date]:
    today = datetime.today()
    from_day4 = date(year=(today.year - 2), month=4, day=1)
    to_day4 = date(year=today.year, month=3, day=31)
    from_day10 = date(year=(today.year - 2), month=10, day=1)
    to_day10 = date(year=today.year, month=9, day=30)
    if today.month in [4, 5, 6, 7, 8, 9]:
        return from_day10, to_day10
    else:
        return from_day4, to_day4


def get_concerned_users(staff_id: int):
    concerned_user_list = []

    base_from, base_to = config_from_to_holiday()
    holiday_calculator = HolidayDayCount(staff_id)
    user_base_day: datetime = HolidayDayCount.convert_base_day(
        holiday_calculator.in_day
    )
    if user_base_day.month == base_from.month:  # 本番は==にします
        concerned_user_list.append(staff_id)

    return concerned_user_list


"""
Calculate the sum of leave days based on API data.
    @param
        api_data: Dict[str, float] Dictionary containing leave data.
    @return
        : float Total leave days.
"""


def calc_leave_sum_days(api_data: Dict[str, float]) -> float:
    celing = math.ceil

    # used_times: int = 0
    # APIデータから時間休と中抜けの合計を計算
    leave_times = api_data.get("hourly_leave") + api_data.get("half_hour_leave")
    print(
        f"leave_times={leave_times} / contract_vacation_hours={api_data.get('contract_vacation_hours')}"
    )  # デバッグ用
    if leave_times == 0:
        used_convert_days = 0
    else:
        # 時間休と中抜けを契約休暇時間で割って、切り上げて日数に変換
        used_convert_days = celing(
            leave_times / api_data.get("contract_vacation_hours")
        )

    sum_leave_days: float = (
        api_data["leave_full"] + api_data["leave_half"] / 2 + used_convert_days
    )

    return sum_leave_days


def calculate_prev_carry(api_prev_data_list) -> Dict[int, dict]:
    """
    全staff_id分の繰り越し日数を一括計算
    :param api_prev_data_list: List[dict]
    :return: dict {staff_id: carry_over}
    """
    staff_data = defaultdict(list)
    # staff_idごとにデータをまとめる
    for data in api_prev_data_list:
        staff_data[data["staff_id"]].append(data)

    prev_result_dict = {}
    for staff_id, items in staff_data.items():
        hc = HolidayDayCount(id=staff_id)
        if staff_id in get_concerned_users(staff_id):
            grant = hc.get_valid_holidays()[0]
            used_sum = sum(calc_leave_sum_days(d) for d in items)
            prev_result_dict[staff_id] = grant - used_sum
            used_sum = sum(calc_leave_sum_days(d) for d in items)
            # result[f"{staff_id}"] = grant_sum - used_sum
            prev_result_dict[staff_id] = {"付与日数": grant, "使用日数": used_sum}
        else:
            print(f"ID{staff_id}: 対象外のユーザー({hc.in_day})です。")

    return prev_result_dict


def calculate_carry_over_all(api_data_list) -> Dict[int, dict]:
    """
    全staff_id分の繰り越し日数を一括計算
    :param api_data_list: List[dict]
    :return: dict {staff_id: carry_over}
    """
    staff_data = defaultdict(list)
    # staff_idごとにデータをまとめる
    for data in api_data_list:
        staff_data[data["staff_id"]].append(data)

    result = {}
    for staff_id, items in staff_data.items():
        hc = HolidayDayCount(id=staff_id)
        if staff_id in get_concerned_users(staff_id):
            workday_count_list = (
                hc.get_valid_holidays()[1:]
                if len(hc.get_valid_holidays()) == 3
                else hc.get_valid_holidays()
            )
            # workday_count_list = hc.get_valid_holidays()
            grant_sum = sum(workday_count_list)
            print(f"ID{staff_id}: 付与日数: {grant_sum}")
            used_sum = sum(calc_leave_sum_days(d) for d in items)
            # result[f"{staff_id}"] = grant_sum - used_sum
            result[staff_id] = {
                "付与日数": grant_sum,
                "使用日数": used_sum,
            }
        else:
            print(f"ID{staff_id}: 対象外のユーザー({hc.in_day})です。")
            # result[staff_id] = {
            #     "付与日数": {hc.in_day.strftime("%Y-%m-%d")},
            #     "使用日数": 0,
            # }
    return result
