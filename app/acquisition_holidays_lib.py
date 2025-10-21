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
            deal_work_count = holiday_count_obj.count_recent_workdays()
            next_acquire_holidays = holiday_count_obj.select_next_holiday(
                deal_work_count
            )

            from_now_on_acquire_dict[activate_staff.STAFFID] = {
                "in_day": holiday_count_obj.in_day,
                "recent_work_count": deal_work_count,
                "from_now_on_grant": next_acquire_holidays,
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
