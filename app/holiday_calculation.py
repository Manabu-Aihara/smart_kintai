from datetime import date, datetime
from dataclasses import dataclass
from typing import List, Tuple, Union
from collections import OrderedDict
from monthdelta import monthmod
from dateutil.relativedelta import relativedelta

from sqlalchemy import or_, and_

from . import db
from .database_base import session
from .models import (
    StaffHolidayContract,
    StaffJobContract,
    Contract,
    User,
    RecordPaidHoliday,
    Attendance,
)
from .acquisition_type import divide_acquire_type, AcquisitionType
from .new_calendar import NewCalendar
from .holiday_logging import HolidayLogger


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
class HolidayCalculate:
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

    """
    入職日から次回付与日までの年休付与日数を取得
    @Param
        work_count: int 勤務日数
    @Return
        holiday_pair: OrderedDict<date, int>
    """

    def acquire_holidays_dict(self, work_count: int) -> OrderedDict[date, int]:
        base_day = self.convert_base_day(self.in_day)
        # 次回付与日を含む
        day_list = [self.in_day.date()] + self.get_acquisition_list(base_day)
        holiday_pair = self.acquire_inday_holidays()

        for i, acquisition_day in enumerate(
            AcquisitionType.name(divide_acquire_type(work_count)).under5y, 1
        ):
            if i == len(day_list):
                break
            else:
                holiday_pair[day_list[i]] = acquisition_day

        # 入職5年以上くらい
        if len(day_list) > len(
            AcquisitionType.name(divide_acquire_type(work_count)).under5y
        ):
            for day in day_list[7:]:
                holiday_pair[day] = AcquisitionType.name(
                    divide_acquire_type(work_count)
                ).onward
        # except KeyError as e:
        #     logger = HolidayLogger.get_logger("ERROR", "-err")
        #     logger.error(f"ID{self.id}: {work_count}, {e}", exc_info=False)
        # else:
        return holiday_pair

    # 表示用: STARTDAY, ENDDAYのペア
    def print_acquisition_data(self) -> Tuple[list[date], list[date]]:
        base_day = self.convert_base_day(self.in_day)
        day_list = [self.in_day.date()] + self.get_acquisition_list(base_day)

        end_day_list = [
            end_day + relativedelta(years=1, days=-1) for end_day in day_list
        ]
        end_day_list[0] = self.get_acquisition_list(base_day)[0] + relativedelta(
            days=-1
        )
        return (day_list, end_day_list)

    """
    出退勤による勤務日数、範囲は付与前の直近2、3期間分
    3月、9月末に起動
    """

    def count_workdays(self) -> List[int]:
        base_day = self.convert_base_day(self.in_day)
        """
        直近2、3期間分の勤務日数リストを返す（DBクエリは1回のみ）
        """
        from_list, to_list = self.print_acquisition_data()
        recent_from: List[date] = []
        recent_to: List[date] = []
        # 入職日〜3期間
        if len(self.get_acquisition_list(base_day)) <= 4:
            if (
                get_calendar_nth_dow(
                    self.in_day.year, self.in_day.month, self.in_day.day
                )
                != 1
            ):
                # 入職日が第1週でなければ、翌月からカウント（今のところ私の独断）
                middle_in_day = from_list[0] + relativedelta(months=1)
                recent_from = [middle_in_day.replace(day=1)] + from_list[1:-2]
                recent_to = to_list[:-2]
            else:
                # print_acquisition_dataは、末尾は翌付与日からの範囲なので、2つ前まで
                recent_from = from_list[:-2]
                recent_to = to_list[:-2]
                print(f"Debug type: {recent_from}")
        # 4期間以上
        elif len(self.get_acquisition_list(base_day)) > 4:
            recent_from = from_list[-5:-2]
            recent_to = to_list[-5:-2]

        # print(
        #     f"ID{self.id}: count_workday > : 勤務日数を取得します。期間: {recent_from[0]} ~ {recent_to[-1]}"
        # )

        # # 入職日年休付与以外、受けていない者（付与日リストが1個だけ）
        # if (len(self.get_acquisition_list(base_day)) == 1) and (
        #     get_calendar_nth_dow(self.in_day.year, self.in_day.month, self.in_day.day)
        #     != 1
        # ):
        #     # 入職日が第1週でなければ、翌月からカウント（今のところ私の独断）
        #     middle_in_day = from_list[0] + relativedelta(months=1)
        #     overall_start = middle_in_day.replace(day=1)
        #     overall_end = recent_to[-1]
        # else:
        #     # 直近2期間の開始日・終了日で全件一括取得
        #     # overall_start = from_list[-2] と同じ
        overall_start = recent_from[0]
        overall_end = to_list[-1]

        n_absence_list: List[str] = ["8", "17", "18", "19", "20"]

        filters = [
            Attendance.STAFFID == self.id,
            Attendance.WORKDAY >= overall_start,
            Attendance.WORKDAY <= overall_end,
            Attendance.NOTIFICATION.notin_(n_absence_list),
            # Attendance.NOTIFICATIONが"3"または"5", "9"の場合は、
            # Attendance.STARTTIME != "00:00"の条件を適用しない
            # → つまり、NOTIFICATIONが"3"または"5", "9"なら除外条件なし、それ以外は除外条件あり
            # 「Attendance.STARTTIME != '00:00'」の条件を、
            # 「NOTIFICATIONが'3'または'5', "9"のときは適用しない」
            or_(
                Attendance.NOTIFICATION.in_(["3", "5", "9"]),
                and_(
                    ~Attendance.NOTIFICATION.in_(["3", "5", "9"]),
                    Attendance.STARTTIME != "00:00",
                ),
            ),
        ]
        all_attendance = session.query(Attendance.WORKDAY).filter(*filters).all()

        # Python側で各期間ごとにカウント（2つか3つになる（2025年7月25日））
        work_counts = []
        for i, (start, end) in enumerate(zip(recent_from, recent_to)):
            print(
                f"ID{self.id}: count_workday > : 勤務日数を取得します。期間: {start} ~ {end}"
            )
            count = sum(1 for (day,) in all_attendance if start <= day <= end)
            print(
                f"ID{self.id}: count_workday > : 勤務日数をカウントします。日数: {count} "
            )
            work_counts.append(count)

        # work_counts[-1] = round(work_counts[-1] * 6 / 5)
        # print(f"Last count: {work_counts[-1]}")

        # logger = HolidayLogger.get_logger("INFO")
        # logger.info(f"ID{self.id}: count: 勤務日数は{work_counts}日です。")

        print(f"Work count: {work_counts}")
        return work_counts

    """ 入職日年休付与以外受けていない人対応 """
    """
    @Return
        : int 入職月（場合によって+1）と基準月との差、2〜5
        """

    def get_diff_month(self) -> int:
        base_day = self.convert_base_day(self.in_day)

        # 入職日〜基準日1日前
        diff_month = monthmod(self.in_day, base_day + relativedelta(days=-1))[0].months
        # 入職日が第1週でなければ、翌月からカウント（今のところ私の独断）
        result_diff = (
            diff_month + 1
            if get_calendar_nth_dow(
                self.in_day.year, self.in_day.month, self.in_day.day
            )
            == 1
            else diff_month
        )

        # print(f"ID{self.id}: (入職日以外の)初の年休支給になります。")
        logger = HolidayLogger.get_logger("INFO", "-info")
        logger.info(f"ID{self.id}: {result_diff}ヶ月分を12ヶ月にしてカウントします。")

        return result_diff

    def count_workday_half_year(self) -> int:
        # 入職月〜基準月1日前の範囲を12ヶ月分にしたもの
        workday_half_result = self.count_workdays()[0] * (12 / self.get_diff_month())
        workday_half_result = round(workday_half_result)

        logger = HolidayLogger.get_logger("INFO", "-info")
        logger.info(
            f"ID{self.id}: count_half > : 暫定勤務日数は{workday_half_result}日です。"
        )

        return workday_half_result

    """
    〜3年遡って付与された日数のリスト
    @Return
        : list<int> 付与日数リスト
        """

    def get_valid_holidays(self) -> List[int]:
        holiday_list = []
        if len(self.get_acquisition_list(self.convert_base_day(self.in_day))) == 1:
            # 入職日年休付与以外受けていない人
            holiday_list = list(self.acquire_inday_holidays().values())  # 1個
        elif len(self.get_acquisition_list(self.convert_base_day(self.in_day))) == 2:
            # 入職日含め、付与2回受けている人
            work_counts_half_ajust = self.count_workday_half_year()
            # work_counts = self.count_workdays()
            holiday_list = list(self.acquire_inday_holidays().values())
            # for idx, count in enumerate([work_counts_half_ajust]):
            print(
                f"Acquisition date days =3: {self.acquire_holidays_dict(work_counts_half_ajust)}"
            )
            holiday_list.append(
                list(self.acquire_holidays_dict(work_counts_half_ajust).values())[1]
            )  # 2個
        elif len(self.get_acquisition_list(self.convert_base_day(self.in_day))) == 3:
            # 入職日含め、付与3回受けている人
            work_counts_half_ajust = self.count_workday_half_year()
            work_counts = self.count_workdays()
            holiday_list = list(self.acquire_inday_holidays().values())
            for idx, count in enumerate([work_counts_half_ajust] + work_counts[1:]):
                print(f"Acquisition date days =4: {self.acquire_holidays_dict(count)}")
                acquisition_days = list(self.acquire_holidays_dict(count).values())[
                    -3 + idx
                ]
                holiday_list.append(acquisition_days)  # 3個
        elif len(self.get_acquisition_list(self.convert_base_day(self.in_day))) > 3:
            # 付与4回以上
            work_counts = self.count_workdays()
            for idx, count in enumerate(work_counts):
                print(f"Acquisition date days >4: {self.acquire_holidays_dict(count)}")
                acquisition_days = list(self.acquire_holidays_dict(count).values())[
                    -4 + idx
                ]
                holiday_list.append(acquisition_days)  # 3個

        return holiday_list
