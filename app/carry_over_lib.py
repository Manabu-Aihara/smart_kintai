import math
from datetime import date, datetime
from typing import Tuple, Dict, Any
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


def get_concerned_user_object(staff_id: int) -> HolidayDayCount:
    base_from, base_to = config_from_to_holiday()
    holiday_count_obj_for_staff = HolidayDayCount(staff_id)
    user_base_day: datetime = HolidayDayCount.convert_base_day(
        holiday_count_obj_for_staff.in_day
    )
    if user_base_day.month == base_from.month:  # 本番は==にします
        return holiday_count_obj_for_staff
    return None


"""
Calculate the sum of leave days based on API data.
    @param
        api_data: Dict[str, float] Dictionary containing leave data.
    @return
        : float Total leave days.
"""


def calc_leave_sum_days(api_data: Dict[str, float]) -> float:

    sum_leave_days: float = api_data["leave_full"] + api_data["leave_half"] / 2

    return sum_leave_days


def calc_leave_sum_times(api_data: Dict[str, float]) -> Tuple[float, float]:
    celing = math.ceil
    # used_times: int = 0
    # APIデータから時間休と中抜けの合計を計算
    leave_times = api_data.get("hourly_leave") + api_data.get("half_hour_leave")
    # print(
    #     f"leave_times={leave_times} / contract_vacation_hours={api_data.get('contract_vacation_hours')}"
    # )  # デバッグ用
    # if leave_times == 0:
    #     used_convert_days = 0
    # else:
    #     # 時間休と中抜けを契約休暇時間で割って、切り上げて日数に変換
    #     used_convert_days = celing(
    #         leave_times / api_data.get("contract_vacation_hours")
    #     )

    return leave_times, api_data.get("contract_vacation_hours")


# 一年後とか使えるかも
# def calculate_prev_carry(api_prev_data_list) -> Dict[int, dict]:
#     """
#     全staff_id分の繰り越し日数を一括計算
#     :param api_prev_data_list: List[dict]
#     :return: dict {staff_id: carry_over}
#     """
#     staff_data = defaultdict(list)
#     # staff_idごとにデータをまとめる
#     for data in api_prev_data_list:
#         staff_data[data["staff_id"]].append(data)

#     prev_result_dict = {}
#     for staff_id, items in staff_data.items():
#         hc = HolidayDayCount(id=staff_id)
#         if staff_id in get_concerned_users(staff_id):
#             grant = hc.get_valid_holidays()[0]
#             used_sum = sum(calc_leave_sum_days(d) for d in items)
#             prev_result_dict[staff_id] = grant - used_sum
#             used_sum = sum(calc_leave_sum_days(d) for d in items)
#             # result[f"{staff_id}"] = grant_sum - used_sum
#             prev_result_dict[staff_id] = {"付与日数": grant, "使用日数": used_sum}
#         else:
#             print(f"ID{staff_id}: 対象外のユーザー({hc.in_day})です。")

#     return prev_result_dict
# print("Calculating carry over for all staff members...")


def calculate_carry_over_all(api_data_list) -> Dict[int, Dict[str, Any]]:
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
        holiday_count_obj = get_concerned_user_object(staff_id)
        if holiday_count_obj:
            grant_list = (
                holiday_count_obj.get_valid_holidays()[1:]
                if len(holiday_count_obj.get_valid_holidays()) == 3
                else holiday_count_obj.get_valid_holidays()
            )
            # workday_count_list = hc.get_valid_holidays()
            grant_sum = sum(grant_list)
            print(f"ID{staff_id}: 付与日数: {grant_sum}")
            # used_sum = sum(calc_leave_sum_days(d) for d in items)
            used_leave_days = [calc_leave_sum_days(d) for d in items]
            used_leave_times, contract_vacation_hours = zip(
                *[calc_leave_sum_times(d) for d in items]
            )
            # result[f"{staff_id}"] = grant_sum - used_sum
            result[staff_id] = {
                "付与日数": grant_list,
                "使用年休": used_leave_days,
                "使用時間休": used_leave_times,
                "契約休暇時間": contract_vacation_hours,
            }
        else:
            print(f"ID{staff_id}: 対象外のユーザーです。")
            # result[staff_id] = {
            #     "付与日数": {hc.in_day.strftime("%Y-%m-%d")},
            #     "使用日数": 0,
            # }
    return result
