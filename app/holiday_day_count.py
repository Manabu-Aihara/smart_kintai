from datetime import date
from dataclasses import dataclass, field
from typing import List, Tuple, Dict
from collections import OrderedDict
from monthdelta import monthmod
from dateutil.relativedelta import relativedelta

from sqlalchemy import or_, and_

from . import db
from .models import Attendance
from .holiday_base import HolidayBase, get_calendar_nth_dow
from .acquisition_type import divide_acquire_type, AcquisitionType
from .holiday_logging import HolidayLogger


@dataclass
class HolidayDayCount(HolidayBase):
    # スタッフID
    # id: int

    def __post_init__(self):
        try:
            super().__post_init__()
        except TypeError as e:
            raise e

    """
    メソッド名の目安
    acquire: 日数
    get: 日付
    """

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
                print(f"△Debug type: {recent_from}")
            else:
                # print_acquisition_dataは、末尾は翌付与日からの範囲なので、2つ前まで
                recent_from = from_list[:-2]
                recent_to = to_list[:-2]
                print(f"▲Debug type: {recent_from}")
        # 4期間以上
        elif len(self.get_acquisition_list(base_day)) > 4:
            recent_from = from_list[-5:-2]
            recent_to = to_list[-5:-2]

        overall_start = recent_from[0]
        overall_end = to_list[-1]

        n_absence_list: List[str] = ["8", "17", "18", "19", "20"]

        filters = [
            Attendance.STAFFID == self.id,
            Attendance.WORKDAY >= overall_start,
            Attendance.WORKDAY <= overall_end,
            Attendance.NOTIFICATION.notin_(n_absence_list),
            # 除外条件: Attendance.STARTTIME != '00:00'
            # Attendance.NOTIFICATIONが"3"または"5", "9"の場合は、Attendance.STARTTIME != "00:00"の条件を適用しない
            # → つまり、NOTIFICATIONが"3"または"5", "9"なら除外条件なし、それ以外は除外条件あり
            or_(
                Attendance.NOTIFICATION.in_(["3", "5", "9"]),
                and_(
                    ~Attendance.NOTIFICATION.in_(["3", "5", "9"]),
                    Attendance.STARTTIME != "00:00",
                ),
            ),
        ]
        all_attendance = db.session.query(Attendance.WORKDAY).filter(*filters).all()

        # Python側で各期間ごとにカウント（2つか3つになる（2025年7月25日そう判断））
        work_counts = []
        for i, (start, end) in enumerate(zip(recent_from, recent_to)):
            print(
                f"ID{self.id}: count_workday > : 勤務期間を取得します。期間: {start} ~ {end}"
            )
            count = sum(1 for (day,) in all_attendance if start <= day <= end)
            print(
                f"ID{self.id}: count_workday > : 勤務日数をカウントします。日数: {count} "
            )
            work_counts.append(count)

        # logger = HolidayLogger.get_logger("INFO")
        # logger.info(f"ID{self.id}: count: 勤務日数は{work_counts}日です。")
        if base_day.month == 4:
            provisional_work_count = work_counts[0] * 4 / 3
            work_counts[0] = round(provisional_work_count)
            print(f"Debug provisional work count: {work_counts[0]}")

        print(f"Work count: {work_counts}")
        return work_counts

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
        # bug = "Empty" if len(self.count_workdays()) == 0 else self.count_workdays()
        # print(f"Debug: {self.id} - {bug}")
        # 入職月〜基準月1日前の範囲を12ヶ月分にしたもの
        workday_half_result = self.count_workdays()[0] * (12 / self.get_diff_month())
        workday_half_result = round(workday_half_result)

        logger = HolidayLogger.get_logger("INFO", "-info")
        logger.info(
            f"ID{self.id}: count_half > : 暫定勤務日数は{workday_half_result}日です。"
        )

        return workday_half_result

    def get_next_holiday_pair(self) -> Tuple[int, int]:
        from_list, to_list = self.print_acquisition_data()
        base_day = self.convert_base_day(self.in_day)
        # 一ヶ月の猶予を設ける
        today = date.today()
        if today.month == base_day.month:
            start_of_range = from_list[-3]
            end_of_range = to_list[-3]
        else:
            start_of_range = from_list[-2]
            end_of_range = to_list[-2]

        n_absence_list: List[str] = ["8", "17", "18", "19", "20"]

        filters = [
            Attendance.STAFFID == self.id,
            Attendance.WORKDAY >= start_of_range,
            Attendance.WORKDAY <= end_of_range,
            Attendance.NOTIFICATION.notin_(n_absence_list),
            # Attendance.STARTTIME == '00:00'の場合、除かれる
            # Attendance.NOTIFICATIONが"3"または"5", "9"の場合は、
            # Attendance.STARTTIME != "00:00"の条件を適用しない
            # → つまり、NOTIFICATIONが"3"または"5", "9"なら除外条件なし、それ以外は除外条件あり
            # 「NOTIFICATIONが'3'または'5', "9"のときは適応」
            or_(
                Attendance.NOTIFICATION.in_(["3", "5", "9"]),
                and_(
                    ~Attendance.NOTIFICATION.in_(["3", "5", "9"]),
                    Attendance.STARTTIME != "00:00",
                ),
            ),
        ]
        work_count = db.session.query(Attendance.WORKDAY).filter(*filters).count()

        if len(self.get_acquisition_list(base_day)) == 2:
            work_count = self.count_workday_half_year()

        next_holiday = (
            list(self.acquire_holidays_dict(work_count).values())[-2]
            if today.month == base_day.month
            else list(self.acquire_holidays_dict(work_count).values())[-1]
        )

        return work_count, next_holiday

    """
    〜3年遡って付与された日数のリスト
    @Return
        : list<int> 付与日数リスト
        """

    def get_valid_holidays(self) -> List[int]:
        base_day = self.convert_base_day(self.in_day)

        holiday_list = []
        if len(self.get_acquisition_list(base_day)) == 1:
            # 入職日年休付与以外受けていない人
            holiday_list = list(self.acquire_inday_holidays().values())  # 1個
        elif len(self.get_acquisition_list(base_day)) == 2:
            # 入職日含め、付与2回受けている人
            work_counts_half_ajust = self.count_workday_half_year()
            holiday_list = list(self.acquire_inday_holidays().values())  # 入職日付与
            print(
                f"Acquisition date/days =3: {self.acquire_holidays_dict(work_counts_half_ajust)}"
            )
            holiday_list.append(
                list(self.acquire_holidays_dict(work_counts_half_ajust).values())[1]
            )  # 2個
        elif len(self.get_acquisition_list(base_day)) == 3:
            # 入職日含め、付与3回受けている人
            work_counts_half_ajust = self.count_workday_half_year()
            work_counts = self.count_workdays()
            holiday_list = list(self.acquire_inday_holidays().values())  # 入職日付与
            for idx, count in enumerate([work_counts_half_ajust] + work_counts[1:]):
                print(f"Acquisition date/days =4: {self.acquire_holidays_dict(count)}")
                acquisition_days = list(self.acquire_holidays_dict(count).values())[
                    -3 + idx
                ]
                holiday_list.append(acquisition_days)  # 4個
        elif len(self.get_acquisition_list(base_day)) == 4:
            # 付与4回以上
            work_counts_half_ajust = self.count_workday_half_year()
            work_counts = self.count_workdays()
            for idx, count in enumerate([work_counts_half_ajust] + work_counts[1:]):
                print(f"Acquisition date/days >4: {self.acquire_holidays_dict(count)}")
                acquisition_days = list(self.acquire_holidays_dict(count).values())[
                    -4 + idx
                ]
                holiday_list.append(acquisition_days)  # 3個
        elif len(self.get_acquisition_list(base_day)) >= 5:
            # 付与5回以上
            work_counts = self.count_workdays()
            for idx, count in enumerate(work_counts):
                print(f"Acquisition date/days >5: {self.acquire_holidays_dict(count)}")
                acquisition_days = list(self.acquire_holidays_dict(count).values())[
                    -4 + idx
                ]
                holiday_list.append(acquisition_days)  # 3個

        return holiday_list


@dataclass
class HolidayCountFactory:
    _instances: Dict[int, "HolidayDayCount"] = field(default_factory=dict)

    def get_instance(self, staff_id: int) -> "HolidayDayCount":
        if staff_id not in self._instances:
            self._instances[staff_id] = HolidayDayCount(staff_id)
        return self._instances[staff_id]
