from typing import Dict, Any
from datetime import datetime

from sqlalchemy import and_, func

from . import db
from .select_only_sync import read_session
from .models import User
from .models_aprv import PaidHolidayLog
from .holiday_day_count import HolidayDayCount
from .carry_over_lib import config_from_to_holiday

"""
    各ユーザーの入職日、1年間の勤務日数、これからの有休付与日数を取得
    @Return
        : Dict[int, Dict[str, Any]]
    """


def acquire_holidays_from_now() -> Dict[int, Dict[str, Any]]:
    from_now_on_acquire_dict = {}
    activate_staff_list = (
        db.session.query(User.STAFFID)
        .filter(
            and_(
                User.DISPLAY == 0,
                User.STAFFID != 10000,
                User.STAFFID != 224,
                User.STAFFID != 246,
            )
        )
        .all()
    )
    base_from, base_to = config_from_to_holiday()
    for activate_staff in activate_staff_list:
        try:
            holiday_count_obj = HolidayDayCount(activate_staff.STAFFID)
            user_base_date: datetime = HolidayDayCount.convert_base_day(
                holiday_count_obj.in_day
            )
        except TypeError as e:
            raise e

        if base_from.month == user_base_date.month:
            work_counts: list[int] = holiday_count_obj.count_workdays()
            arg_work_count: int = 0
            if len(holiday_count_obj.get_acquisition_list(user_base_date)) == 2:
                arg_work_count = holiday_count_obj.count_workday_half_year()
                print(f"It's pass half work count. {arg_work_count}")
            else:
                arg_work_count = (
                    work_counts[-1]
                    # 一ヶ月の猶予を設ける
                    # if base_from.month in [4, 10] and len(work_counts) > 2
                    # else work_counts[-1]
                )
            # 付与日と付与日数
            date_and_holidays = holiday_count_obj.acquire_holidays_dict(arg_work_count)
            # これからの付与日数
            print(f"Acquisition days: {list(date_and_holidays.values())[-1]}")
            from_now_on_holidays = (
                list(date_and_holidays.values())[-2]
                # 一ヶ月の猶予を設ける
                # if base_from.month in [4, 10]
                # else list(date_and_holidays.values())[-1]
            )
            from_now_on_acquire_dict[activate_staff.STAFFID] = {
                "in_day": holiday_count_obj.in_day,
                "recent_work_count": arg_work_count,
                "from_now_on_grant": from_now_on_holidays,
            }

    return from_now_on_acquire_dict


"""
    各ユーザーの直近の有休記録（クエリー）を取得
    @Return
        : List[PaidHolidayLog]
    """


async def get_last_paid_holiday_logs():
    subquery = (
        read_session.query(PaidHolidayLog.STAFFID, func.max(PaidHolidayLog.id))
        .group_by(PaidHolidayLog.STAFFID)
        .subquery()
    )
    paid_holiday_log_list = (
        read_session.query(PaidHolidayLog)
        .join(subquery, PaidHolidayLog.id == subquery.c.max)
        .all()
    )

    return paid_holiday_log_list
