from typing import Dict, List, Any
from datetime import datetime

from .database_base import session
from .models import User
from .models_aprv import PaidHolidayLog
from .holiday_day_count import HolidayDayCount
from .carry_over_lib import config_from_to_holiday


def acquire_holidays_from_now(staff_id: int) -> Dict[str, Any]:
    holiday_count_obj = HolidayDayCount(staff_id)
    recent_work_count = holiday_count_obj.count_recent_workdays()
    date_and_holidays = holiday_count_obj.acquire_holidays_dict(recent_work_count)
    from_now_on_holidays = list(date_and_holidays.values())[-1]
    log_input_dict = {
        # "staff_id": staff_id,
        "in_day": holiday_count_obj.in_day,
        "recent_work_count": recent_work_count,
        "from_now_on_grant": from_now_on_holidays,
    }
    return log_input_dict


def get_concerned_members() -> List[int]:
    concerned_members = []
    activate_staff_list = session.query(User.STAFFID).filter(User.DISPLAY == 0).all()
    base_from, base_to = config_from_to_holiday()
    for activate_staff in activate_staff_list:
        holiday_count_obj = HolidayDayCount(activate_staff.STAFFID)
        user_base_date: datetime = HolidayDayCount.convert_base_day(
            holiday_count_obj.in_day
        )
        if base_from.month == user_base_date.month:
            concerned_members.append(activate_staff.STAFFID)

    return concerned_members


def add_acquisition_data() -> None:
    try:
        for concerned_staff in get_concerned_members():
            holiday_info_dict = acquire_holidays_from_now(concerned_staff)
            from_now_on_holidays: int = holiday_info_dict.get("from_now_on_grant", 0)
            print(f"Debug: {concerned_staff} → {from_now_on_holidays}日")
            add_data = PaidHolidayLog(
                concerned_staff, from_now_on_holidays, None, None, None, None
            )
            session.add(add_data)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
