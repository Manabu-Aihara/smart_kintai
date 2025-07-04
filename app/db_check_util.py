from typing import Optional, Callable

from . import db
from .models import User, StaffJobContract, RecordPaidHoliday, Contract

"""
    User, StaffJobContract間の値の違いを指摘
    @Param
        target_id: int 目的のスタッフID
    @Return
        target_id: int | None 該当のスタッフID
    """


def check_contract_value(target_id: int) -> Optional[int]:
    target_staff_info = (
        db.session.query(User.CONTRACT_CODE, User.JOBTYPE_CODE)
        .filter(User.STAFFID == target_id)
        .first()
    )
    target_contract_info = (
        db.session.query(StaffJobContract.CONTRACT_CODE, StaffJobContract.JOBTYPE_CODE)
        .filter(StaffJobContract.STAFFID == target_id)
        .order_by(StaffJobContract.START_DAY.desc())
        .first()
    )
    if target_contract_info is None:
        raise TypeError("There is not in StaffJobContract")
    else:
        if (
            target_staff_info.CONTRACT_CODE != target_contract_info.CONTRACT_CODE
            or target_staff_info.JOBTYPE_CODE != target_contract_info.JOBTYPE_CODE
        ):
            # raise ValueError("テーブル間で、雇用形態及び勤務形態が合致していません")
            return target_id
        else:
            return None


""" 以下そのうち使えるかなデコレーター """


def _check_error_handler(func):
    def wrapper(staff_id: int, *args, **kwargs):
        try:
            print(args)
            value = check_contract_value(staff_id)
        except TypeError as e:
            print(e)
        # except ValueError as e:
        #     print(f"{staff_id}: {e}")
        else:
            return func(value, *args, **kwargs)

    wrapper.__name__ = func.__name__
    return wrapper


def check_error_handler(func):
    def wrapper(*args, **kwargs):
        try:
            return func(args, kwargs)
        except TypeError as e:
            print(e)
        except ValueError as e:
            print(e)

    wrapper.__name__ = func.__name__
    return wrapper


""" ここまで """

"""
    RecordPaidHoliday, StaffJobContract間の値の違いを指摘
    以下check_contract_valueと変わらず
    """


def check_basetime_value(target_id: int) -> Optional[int]:
    target_paid_holiday_basetime: float = (
        db.session.query(RecordPaidHoliday.BASETIMES_PAIDHOLIDAY)
        .filter(RecordPaidHoliday.STAFFID == target_id)
        .first()
    )
    # あえてUserではなく、契約情報からにした
    target_contract_user = db.session.get(StaffJobContract, target_id)
    contract_worktime: float = (
        db.session.query(Contract.WORKTIME)
        .filter(Contract.CONTRACT_CODE == target_contract_user.CONTRACT_CODE)
        .first()
    )
    contract_part_worktime: float = target_contract_user.PART_WORKTIME
    if target_contract_user is None:
        raise TypeError("There is not in StaffJobContract")
    elif contract_part_worktime == 0.0:
        if target_paid_holiday_basetime != contract_worktime:
            return target_id
        else:
            return None
    else:
        if target_paid_holiday_basetime != contract_part_worktime:
            return target_id
        else:
            return None


# 時期に、関数をチョイスできるよう引数を増やす予定
def compare_db_item(staff_id: int, func: Callable[..., int]) -> int:
    try:
        caution_id = func(staff_id)
    except TypeError as e:
        print(f"{e}: {staff_id}")
    else:
        return caution_id
