from datetime import date, datetime
from dataclasses import dataclass
from typing import List
from collections import OrderedDict
from monthdelta import monthmod
from dateutil.relativedelta import relativedelta

from . import db
from .database_base import session
from .models import (
    StaffHolidayContract,
    StaffJobContract,
    Contract,
    User,
    RecordPaidHoliday,
)
from .new_calendar import NewCalendar


# Pythonで任意の日付がその月の第何週目かを取得
# https://note.nkmk.me/python-calendar-datetime-nth-dow/
def get_calendar_nth_dow(in_year: int, in_month: int, in_day: int) -> int:
    # return (self.in_day.day - 1) // 7 + 1
    calendar_obj = NewCalendar(in_year, in_month)
    return calendar_obj.get_nth_dow(in_day)


"""
    第5週、第6週入職日は翌月カウントデコレータ
    基準日変更の可能性を考慮し
    """


def cure_base_day(func):
    def wrapper(in_date: datetime):
        if get_calendar_nth_dow(in_date.year, in_date.month, in_date.day) >= 5:
            in_date = in_date + relativedelta(months=1)
        return func(in_date.replace(day=1))

    return wrapper


@dataclass
class HolidayBase:
    # スタッフID
    id: int
    # 当面、契約変更は考慮しない方向で
    # holiday_base_time: float

    def __post_init__(self):
        print(f"ID{self.id}: HolidayCalculateクラスのインスタンスを作成しました。")
        target_user = session.get(User, self.id)
        user_contract = (
            session.query(StaffJobContract)
            .filter(StaffJobContract.STAFFID == self.id)
            .order_by(StaffJobContract.START_DAY.asc())
            .first()
        )
        if target_user.INDAY is None:
            self.in_day: datetime = datetime.combine(
                user_contract.START_DAY, datetime.min.time()
            )
        elif target_user.INDAY is not None:
            self.in_day = target_user.INDAY
        else:
            raise TypeError(f"ID{self.id}: 入職日がありません。")

        # 契約休暇時間 holiday_base_time: float
        contract_holiday_time = (
            session.query(StaffHolidayContract.HOLIDAY_TIME)
            .filter(StaffHolidayContract.STAFFID == self.id)
            .order_by(StaffHolidayContract.START_DAY.desc())
            .first()
        )
        alternate_time = (
            session.query(
                RecordPaidHoliday.BASETIMES_PAIDHOLIDAY,
            )
            .filter(self.id == RecordPaidHoliday.STAFFID)
            .first()
        )
        if user_contract.CONTRACT_CODE == 2:
            self.holiday_base_time = (
                contract_holiday_time.HOLIDAY_TIME
                if contract_holiday_time is not None
                else alternate_time.BASETIMES_PAIDHOLIDAY
            )
        else:
            contract_obj = session.get(Contract, user_contract.CONTRACT_CODE)
            self.holiday_base_time = contract_obj.WORKTIME

        if self.holiday_base_time is None:
            raise TypeError(f"ID{self.id}: 契約休暇時間の値がありません。")
            # with open("holiday_err.log", "a") as f:
            #     f.write(
            #         f"{self.id}: D_HOLIDAY_HOSTORY.HOLIDAY_TIME及び、M_RECORD_PAIDHOLIDAY.BASETIMES_PAIDHOLIDAYの値を確認してください。\n"
            #     )

    """
    メソッド名の目安
    acquire: 日数
    get: 日付
    """

    @staticmethod
    @cure_base_day
    def convert_base_day(in_date: datetime) -> datetime:
        # 基準月に変換
        #     入社日が4月〜9月
        #     10月1日に年休付与
        if in_date.month >= 4 and in_date.month < 10:
            change_day = in_date.replace(month=10, day=1)  # 基準月
            return change_day  # 初回付与日

        #     入社日が10月〜12月
        #     翌年4月1日に年休付与
        elif in_date.month >= 10 and in_date.month <= 12:
            change_day = in_date.replace(month=4, day=1)
            return change_day + relativedelta(months=12)

        #     入社日が1月〜3月
        #     4月1日に年休付与
        elif in_date.month < 4:
            change_day = in_date.replace(month=4, day=1)
            return change_day

    """
    付与日のリストを返す（次回付与日を含む）
    @Param
        base_day: datetime 基準日
    @Return
        : List<date>
    """

    def get_acquisition_list(self, base_day: datetime) -> List[date]:
        holidays_get_list = []
        holidays_get_list.append(base_day.date())
        self.base_day = base_day + relativedelta(months=12)
        while base_day < datetime.today():
            if datetime.today() + relativedelta(months=12) < self.base_day:
                break
            return holidays_get_list + self.get_acquisition_list(self.base_day)

        return holidays_get_list
        # 次回付与日
        # return holidays_get_list[-1].date()

    # 初回付与日含めた、付与日のリストを返す
    # base_day = self.convert_base_day()
    # [self.in_day.date()] + self.get_acquisition_list(base_day)

    """
    @Return
        : OrderedDict<date, int> 入職日と支給日数
        """

    def acquire_inday_holidays(self) -> OrderedDict[date, int]:
        base_day = self.convert_base_day(self.in_day)
        # monthmod(inday, datetime.today())[0].months < 2, = 0
        # 入職日から基準日まで1ヶ月以内
        # replace(day=1)しない？
        if monthmod(self.in_day.replace(day=1), base_day)[0].months < 2:
            acquisition_days = 0
        # monthmod(inday, datetime.today())[0].months < 4, < 3
        # 入職日から基準日まで2ヶ月と3ヶ月
        elif monthmod(self.in_day.replace(day=1), base_day)[0].months <= 3:
            acquisition_days = 1
        # monthmod(inday, datetime.today())[0].months < 6, < 5
        # 入職日から基準日まで4ヶ月以上
        elif monthmod(self.in_day.replace(day=1), base_day)[0].months > 3:
            acquisition_days = 2

        first_data = [(self.in_day, acquisition_days)]
        return OrderedDict(first_data)
