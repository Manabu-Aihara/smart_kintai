from typing import Dict

from .holiday_acquisition import HolidayAcquire, AcquisitionType
from .holiday_logging import HolidayLogger


# 付与タイプ（A〜E）から付与日数リスト（under5y, onward）を返す
# 例: get_grant_days_by_type('A', under5y=True) -> [10, 12, 14, 16, 18, 20]
def get_grant_days_by_type(acquire_type: str, under5y: bool = True):
    acq = AcquisitionType.name(acquire_type)
    return acq.under5y if under5y else acq.onward


# BASETIMES_PAIDHOLIDAYのデコレータを使ったエラーハンドリング
def error_handler(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except TypeError as e:
            logger = HolidayLogger.get_logger("ERROR", "-err")
            logger.error(f"ID{args}: {e}", exc_info=False)
            # return float("nan")  # ← ここを追加

    return wrapper


@error_handler
def calcurate_carry_times(api_dict: Dict[str, int]) -> float:
    holiday_acquire_obj = HolidayAcquire(api_dict["staff_id"])

    # APIから得た「時間休」「中抜け」を直接利用
    remainder = (api_dict["hourly_leave"] + api_dict["half_hour_leave"]) % api_dict[
        "contract_vacation_hours"
    ]
    two_years_acquire_times = holiday_acquire_obj.get_sum_holiday(
        api_dict["workday_count"]
    )
    # 最終残り日数を繰り越しにする
    # これは切り捨てる部分 truncate_times
    if remainder == 0:
        truncate_times = 0
    else:
        # base_time - 時間休合計の端数（時間休の合計/base_timeの余り）が切り捨て時間
        truncate_times = holiday_acquire_obj.holiday_base_time - remainder
    # APIから得た「年休全休」「年休半休」を直接利用
    annual_leave_full: float = (
        api_dict["annual_leave_full"] * holiday_acquire_obj.holiday_base_time
    )
    annual_leave_half: float = api_dict["annual_leave_half"] * (
        holiday_acquire_obj.holiday_base_time / 2
    )
    carry_times = two_years_acquire_times - (
        annual_leave_full + annual_leave_half + truncate_times
    )
    return carry_times
