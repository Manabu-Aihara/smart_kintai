import math
from datetime import date, datetime
from typing import Tuple, Dict
from collections import defaultdict

from .acquisition_type import AcquisitionType
from .holiday_calculation import HolidayCalculate
from .holiday_logging import HolidayLogger


# 付与タイプ（A〜E）から付与日数リスト（under5y, onward）を返す
# 例: get_grant_days_by_type('A', under5y=True) -> [10, 12, 14, 16, 18, 20]
def get_grant_days_by_type(acquire_type: str, under5y: bool = True):
    acq = AcquisitionType.name(acquire_type)
    return acq.under5y if under5y else acq.onward


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
    holiday_calculator = HolidayCalculate(staff_id)
    user_base_day: datetime = HolidayCalculate.convert_base_day(
        holiday_calculator.in_day
    )
    if user_base_day.month != base_from.month:
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


def error_handler(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except TypeError as e:
            logger = HolidayLogger.get_logger("ERROR", "-err")
            logger.error(f"ID{args}: {e}", exc_info=False)
            # return float("nan")  # ← ここを追加

    return wrapper


"""
2年消滅ルールに対応した年休繰り越し日数を計算
"""


def calculate_carry_over(api_data_list, staff_id):
    """
    年休繰り越し計算: 複数契約（契約変更）にも対応
    :param api_data_list: List[dict] APIデータリスト（mock_api_data形式）
    :param staff_id: int
    :return: float 繰り越し日数
    """
    # 付与日数: HolidayCalculate.get_valid_holidays の合計
    hc = HolidayCalculate(id=staff_id)
    grant_sum = sum(hc.get_valid_holidays())
    used_sum = 0.0
    for data in api_data_list:
        if data["staff_id"] != staff_id:
            continue
        # 使用日数 = calc_leave_sum_daysで換算
        used_sum += calc_leave_sum_days(data)
    carry_over = grant_sum - used_sum
    return carry_over


@error_handler
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
        hc = HolidayCalculate(id=staff_id)
        if staff_id in get_concerned_users(staff_id):
            grant_sum = sum(hc.get_valid_holidays())
            print(f"ID{staff_id}: 付与日数: {grant_sum}")
            used_sum = sum(calc_leave_sum_days(d) for d in items)
            # result[f"{staff_id}"] = grant_sum - used_sum
            result[staff_id] = {"付与日数": grant_sum, "使用日数": used_sum}
        else:
            print(f"ID{staff_id}: 対象外のユーザー({hc.in_day})です。")
            # result[staff_id] = {
            #     "付与日数": {hc.in_day.strftime("%Y-%m-%d")},
            #     "使用日数": 0,
            # }
    return result
