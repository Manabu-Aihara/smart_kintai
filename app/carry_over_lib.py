import os
import math
import requests
from datetime import date, datetime
from typing import List, Tuple, Dict, Any, OrderedDict, Callable
from collections import defaultdict
import re

from . import db
from .models import Team
from .holiday_day_count import HolidayCountFactory, HolidayDayCount


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
    if user_base_day.month == base_from.month:
        return holiday_count_obj_for_staff
    return None


def retrieve_api_data(url: str) -> List[dict]:
    response = requests.get(url)
    response.raise_for_status()
    api_data_dict = response.json()  # dict形式（この時点で）で取得

    result = []
    for key, item in api_data_dict.items():
        staff_id: str = re.sub(r"(\d{1,4}): (.+)", r"\1", key)
        print(f"Staff ID: {staff_id} / item: {item}")
        extracted = {
            "staff_id": int(staff_id),
            "contract_vacation_hours": item.get("契約休暇（時間）"),
            "leave_full": item.get("年休（全日）"),
            "leave_half": item.get("年休（半日）"),
            "hourly_leave": item.get("時間休"),
            "half_hour_leave": item.get("中抜け"),
        }
        result.append(extracted)

    return result


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


"""
Calculate the sum of leave times and (convert to days based on) contract vacation hours.
    @param
        api_data: Dict[str, float] Dictionary containing leave data.
    @return
        : Tuple[float, float] Total leave times and contract vacation hours.
    """


def calc_leave_sum_times(api_data: Dict[str, float]) -> Tuple[float, float]:
    # ceiling = math.ceil

    # APIデータから時間休と中抜けの合計を計算
    leave_times = api_data.get("hourly_leave") + api_data.get("half_hour_leave")
    print(
        f"leave_times={leave_times} / contract_vacation_hours={api_data.get('contract_vacation_hours')}"
    )  # デバッグ用
    # if leave_times == 0:
    #     used_convert_days = 0 # used_convert_days は一旦保留
    # else:
    #     # 時間休と中抜けを契約休暇時間で割って、切り上げて日数に変換
    #     used_convert_days = ceiling(
    #         leave_times / api_data.get("contract_vacation_hours")
    #     )
    return leave_times, api_data.get("contract_vacation_hours")


def calc_leave_ceiling_times(func: Callable[..., Tuple[float, float]]) -> int:
    leave_times, contract_vacation_hours = func()
    ceiling = math.ceil
    # APIデータから時間休と中抜けの合計を計算
    if leave_times == 0:
        used_convert_days = 0  # used_convert_days は一旦保留
    else:
        # 時間休と中抜けを契約休暇時間で割って、切り上げて日数に変換
        used_convert_days = ceiling(leave_times / contract_vacation_hours)
    return used_convert_days


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
#         holiday_count_obj = get_concerned_user_object(staff_id)
#         if holiday_count_obj:
#             long_ago_grant = holiday_count_obj.get_valid_holidays()[0]
#             print(f"ID{staff_id}: 付与日数: {long_ago_grant}")
#             used_leave_days = [calc_leave_sum_days(d) for d in items]
#             used_leave_times, contract_vacation_hours = zip(
#                 *[calc_leave_sum_times(d) for d in items]
#             )
#             prev_result_dict[staff_id] = {
#                 "付与日数": long_ago_grant,
#                 "使用年休": used_leave_days,
#                 "使用時間休": used_leave_times,
#                 "契約休暇時間": contract_vacation_hours,
#             }
#         else:
#             print(f"ID{staff_id}: 対象外のユーザーです。")

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

    two_years_result_dict = {}
    for staff_id, items in staff_data.items():
        print(f"Debug api items: {items}")
        holiday_count_obj = HolidayDayCount(staff_id)
        if holiday_count_obj:
            granted_dict: OrderedDict[date, int] = (
                holiday_count_obj.get_effective_holidays()
            )
            granted_list = list(granted_dict.values())
            grant_sum = (
                sum(granted_list) if len(granted_list) > 3 else sum(granted_list[:-1])
            )
            print(f"ID{staff_id}: 合計付与日数: {grant_sum}")
            used_leave_days = [calc_leave_sum_days(d) for d in items]
            used_leave_times, contract_vacation_hours = zip(
                *[calc_leave_sum_times(d) for d in items]
            )
            two_years_result_dict[staff_id] = {
                "付与日数": granted_list,
                "使用年休": used_leave_days,
                "使用時間休": used_leave_times,
                "契約休暇時間": contract_vacation_hours,
            }
        else:
            print(f"ID{staff_id}: 対象外のユーザーです。")
    return two_years_result_dict


def fetch_api_server_dict(base_month: str) -> List[dict]:
    team_queries = db.session.query(Team).all()
    shozoku_code_list = [team.CODE for team in team_queries]
    today = datetime.today()
    json_responses = []
    # if today.month == 3:
    #     for shozoku_code in shozoku_code_list:
    #         data_url = f"http://0.0.0.0:8001/frame-data/{shozoku_code}/4"
    #         # data_url = (
    #         #     f"{os.getenv('CLOUD_CALC_PAGE')}/frame-data/{shozoku_code}/4"
    #         # )
    #         api_data_list = retrieve_api_data(data_url)
    #         json_responses.extend(api_data_list)
    # elif today.month == 9:
    #     for shozoku_code in shozoku_code_list:
    #         data_url = f"http://0.0.0.0:8001/frame-data/{shozoku_code}/10"
    #         # data_url = (
    #         #     f"{os.getenv('CLOUD_CALC_PAGE')}/frame-data/{shozoku_code}/10"
    #         # )
    #         api_data_list = retrieve_api_data(data_url)
    #         json_responses.extend(api_data_list)

    # APIデータを、ループで取得するのが好ましくなければ
    if base_month == "4":
        data_url = "http://0.0.0.0:8001/frame-data/0/4/?alert=true"
        # data_url = f"{os.getenv('CLOUD_CALC_PAGE')}/frame-data/0/4/?alert=true"
        api_data_list = retrieve_api_data(data_url)
        json_responses.extend(api_data_list)
    elif base_month == "10":
        data_url = "http://0.0.0.0:8001/frame-data/0/10/?alert=true"
        # data_url = f"{os.getenv('CLOUD_CALC_PAGE')}/frame-data/0/10/?alert=true"
        api_data_list = retrieve_api_data(data_url)
        json_responses.extend(api_data_list)

    return json_responses


"""
    Calculate alert targets for carry-over holidays.
    @param
        api_data_list: List[dict] List of API data dictionaries.
    @return
        : Dict[int, float] Dictionary mapping staff_id to alert value.
"""


def get_alert_target_dict(api_data_list) -> Dict[int, float]:
    ceiling = math.ceil

    staff_data = defaultdict(list)
    # staff_idごとにデータをまとめる
    for data in api_data_list:
        staff_data[data["staff_id"]].append(data)

    holiday_count_obj = HolidayCountFactory()
    notification_dict = {}
    for staff_id, items in staff_data.items():
        print(f"Debug api items: {items}")
        holiday_count_instance = holiday_count_obj.get_instance(staff_id)
        if holiday_count_instance:
            # 年休付与履歴、過去3回分を取得
            granted_dict: OrderedDict[date, int] = (
                holiday_count_instance.get_effective_holidays()
            )
            granted_list = list(granted_dict.values())
            # 2回までなら、パス
            if len(granted_list) < 3:
                notification_dict[staff_id] = 0
                continue
            # リスト4個はないと思うが、一応対応
            granted_sum = sum(
                granted_list
            )  # if len(granted_list) == 3 else sum(granted_list[:-1])
            # 使用全日年休・半休の合計を計算
            used_leave_day_list = [calc_leave_sum_days(d) for d in items]
            # 使用時間休・中抜けの合計を計算
            used_leave_times, contract_vacation_hours = zip(
                *[calc_leave_sum_times(d) for d in items]
            )
            # 時間休・中抜けを日数に変換（切り上げ）
            leave_time_ceil_list = [
                ceiling(l_t / c_t)
                for l_t, c_t in zip(used_leave_times, contract_vacation_hours)
            ]
            used_leave_total = sum(used_leave_day_list) + sum(leave_time_ceil_list)
            remain_value = granted_sum - used_leave_total
            print(f"Grant list and Used: {granted_list} / {used_leave_total}")
            if remain_value > granted_list[-1]:
                alert_value = remain_value - granted_list[-1]
            else:
                alert_value = 0
            notification_dict[staff_id] = alert_value
    return notification_dict
