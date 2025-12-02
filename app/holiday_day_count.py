from datetime import date, datetime
from dataclasses import dataclass, field
from typing import List, Dict
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
            # 入職日が第1週でなければ、翌月からカウント（今のところ私の独断）
            if (
                get_calendar_nth_dow(
                    self.in_day.year, self.in_day.month, self.in_day.day
                )
                != 1
            ):
                middle_in_day = from_list[0] + relativedelta(months=1)
                recent_from = [middle_in_day.replace(day=1)] + from_list[1:-2]
                recent_to = (
                    to_list[:-2]
                    # 以下対象者は一人だが
                    if middle_in_day.month not in [4, 10]
                    else to_list[1:-1]
                )
                print(f"△Debug count period: {recent_from}")
            else:
                # print_acquisition_dateの末尾は、翌付与日なので、3つ前まで
                # 🙅from_list[:-2]、len(from_list) == 2 の場合
                recent_from = [from_list[0]] + from_list[1:-2]
                recent_to = to_list[:-2]
                print(f"▲Debug count period: {recent_from}")
        # 4期間以上
        else:
            recent_from = from_list[-5:-2]
            recent_to = to_list[-5:-2]

        overall_start = recent_from[0]
        # len(to_list) == 2 の場合、空だがエラーにならない
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

        # 暫定の勤務日数を計算（2022年4月1日〜2022年6月30日含めた）
        if overall_start == date(2022, 4, 1):
            provisional_work_count = work_counts[0] * 4 / 3
            work_counts[0] = round(provisional_work_count)
            print(f"Debug provisional work count: {work_counts[0]}")

        # logger = HolidayLogger.get_logger("INFO")
        # logger.info(f"ID{self.id}: count: 勤務日数は{work_counts}日です。")
        print(f"Work count: {work_counts}")
        return work_counts

    """
    @Return
        : int 入職月（場合によって+1）と基準月との差、2〜5
        """

    def get_diff_month(self) -> int:
        base_day = self.convert_base_day(self.in_day)

        # 入職日〜基準日1日前
        first_period_month = monthmod(self.in_day, base_day + relativedelta(days=-1))[
            0
        ].months
        # 入職日が第1週でなければ、翌月からカウント（今のところ私の独断）
        result_diff: int = (
            first_period_month + 1
            if get_calendar_nth_dow(
                self.in_day.year, self.in_day.month, self.in_day.day
            )
            == 1
            else first_period_month
        )

        # print(f"ID{self.id}: (入職日以外の)初の年休支給になります。")
        logger = HolidayLogger.get_logger("INFO", "-info")
        logger.info(f"ID{self.id}: {result_diff}ヶ月分を12ヶ月にしてカウントします。")

        return result_diff

    """
        半年以下の勤務日数を、12ヶ月に換算したものを返す
        @Param
            work_count: int 勤務日数（主に入職してから）
        @Return
            : int 勤務日数
        """

    def count_workday_half_year(self, work_count: int) -> int:
        # 入職月〜基準月1日前の範囲を12ヶ月分にしたもの
        try:
            workday_half_result = work_count * (12 / self.get_diff_month())
        except ZeroDivisionError as e:
            workday_half_result = work_count

        workday_half_result = round(workday_half_result)

        logger = HolidayLogger.get_logger("INFO", "-info")
        logger.info(
            f"ID{self.id}: count_half > : 暫定勤務日数は{workday_half_result}日です。"
        )

        return workday_half_result

    """
        acquire_holidays_dict対応、入職日より半年ずらしたもの
        @Return
            : List<date> 付与日リスト
        """

    def _shift_half_year_list(self) -> List[date]:
        base_day: datetime = self.convert_base_day(self.in_day)

        # 入職日が第1週でなければ、翌月からカウント（今のところ私の独断）
        shift_month = (
            self.in_day.month + 1
            if get_calendar_nth_dow(
                self.in_day.year, self.in_day.month, self.in_day.day
            )
            != 1
            else self.in_day.month
        )

        # 付与日と付与日数は対応していない。入職日の半年先
        shift_date_list = []
        if base_day.month == 4:
            print(f"△Inday: {shift_month}")
            shift_date_list = [
                d + relativedelta(months=shift_month + 2)
                for d in self.get_acquisition_list(base_day)
            ]
        elif base_day.month == 10:
            print(f"▲Inday: {shift_month}")
            shift_date_list = [
                d + relativedelta(months=shift_month - 4)
                for d in self.get_acquisition_list(base_day)
            ]

        return shift_date_list

    """
    入職日から次回付与日増までの年休付与日数を取得
    @Param
        work_count: int 勤務日数
    @Return
        holiday_pair: OrderedDict<date, int>
    """

    def acquire_holidays_dict(self, work_count: int) -> OrderedDict[date, int]:
        base_day: datetime = self.convert_base_day(self.in_day)
        shift_date_list = self._shift_half_year_list()
        # print(f"Shift date list: {shift_date_list}")

        # 次回付与日を含む
        day_list = [
            self.in_day.date(),
            self.get_acquisition_list(base_day)[0],
        ] + shift_date_list

        # 入職日付与[0]番目
        holiday_pair = self.acquire_inday_holidays()

        # 入職5年未満
        for i, acquisition_day in enumerate(
            AcquisitionType.name(divide_acquire_type(work_count)).under5y, 2
        ):
            if i == len(day_list):
                break
            else:
                # print(f"Expect result: {day_list[i]} {acquisition_day}")
                # 3月・9月途中入職に対応
                if i == 2 and (self.in_day.month in [3, 9] and self.in_day.day != 1):
                    holiday_pair[day_list[1]] = AcquisitionType.name("A").under5y[
                        0
                    ]  # 常勤として10日付与
                else:
                    holiday_pair[day_list[i]] = acquisition_day
        print(f"Debug holiday pair under5y: {holiday_pair}")

        # 入職5年以上くらい
        if len(day_list) > len(
            AcquisitionType.name(divide_acquire_type(work_count)).under5y
        ):
            # print("Onward pass.", day_list)
            for day in day_list[8:]:
                holiday_pair[day] = AcquisitionType.name(
                    divide_acquire_type(work_count)
                ).onward
                # print(f"Debug holiday onward date: {day}")
        # except KeyError as e:
        #     logger = HolidayLogger.get_logger("ERROR", "-err")
        #     logger.error(f"ID{self.id}: {work_count}, {e}", exc_info=False)
        # else:
        return holiday_pair

    """
        直近の年休付与に対する、勤務日数をカウント
        @Return
            : int 勤務日数
        """

    def count_recent_workdays(self) -> int:
        base_day = self.convert_base_day(self.in_day)

        from_list, to_list = self.print_acquisition_data()
        # 一ヶ月の猶予を設けるmoratorium
        today = date.today()
        if today.month == base_day.month:
            start_of_range = from_list[-3]
            end_of_range = to_list[-3]
        else:
            start_of_range = from_list[-2]
            end_of_range = to_list[-2]
        print(
            f"ID{self.id}: count_workday > : 勤務期間を取得します。期間: {start_of_range} ~ {end_of_range}"
        )

        if (
            start_of_range == self.in_day
        ):  # and monthmod(start_of_range, end_of_range)[0].months < 6:
            # カウントする範囲が第1週でなければ、翌月から（今のところ私の独断）
            start_of_range = (
                start_of_range + relativedelta(months=1)
                if get_calendar_nth_dow(
                    start_of_range.year, start_of_range.month, start_of_range.day
                )
                != 1
                else start_of_range
            )

        n_absence_list: List[str] = ["8", "17", "18", "19", "20"]

        filters = [
            Attendance.STAFFID == self.id,
            Attendance.WORKDAY >= start_of_range,
            Attendance.WORKDAY <= end_of_range,
            Attendance.NOTIFICATION.notin_(n_absence_list),
            # Attendance.STARTTIME == '00:00'の場合、除かれる
            # Attendance.NOTIFICATIONが"3"または"5", "9"の場合は、Attendance.STARTTIME != "00:00"の条件を適用しない
            # → つまり、NOTIFICATIONが"3"または"5", "9"なら除外条件なし、それ以外は除外条件あり
            # 「NOTIFICATIONが'3'または'5', "9"のときは、Attendance.STARTTIME == '00:00'を適応」
            or_(
                Attendance.NOTIFICATION.in_(["3", "5", "9"]),
                and_(
                    ~Attendance.NOTIFICATION.in_(["3", "5", "9"]),
                    Attendance.STARTTIME != "00:00",
                ),
            ),
        ]
        recent_work_count = (
            db.session.query(Attendance.WORKDAY).filter(*filters).count()
        )
        print(f"△Work count 1: {recent_work_count}")

        if monthmod(self.in_day.date(), end_of_range)[0].months < 6:
            recent_work_count = self.count_workday_half_year(recent_work_count)
            print(f"▲Work count 2: {recent_work_count}")

        return recent_work_count

    """
        count_recent_workdaysで換算された日数を元に、付与日数を取得
        @Param
            recent_work_count: int 直近の年休付与に対する、勤務日数
        @Return
            : int 付与日数
        """

    def select_next_holiday(self, recent_work_count: int) -> int:
        base_day = self.convert_base_day(self.in_day)

        if len(self.get_acquisition_list(base_day)) == 2:
            next_holiday = list(self.acquire_holidays_dict(recent_work_count).values())[
                -2
            ]
        else:
            # 一ヶ月の猶予を設ける
            today = date.today()
            i = -1 if today.month == base_day.month else 0
            # 入職日が4月1日・10月1日なら、対応表通りになる
            next_holiday = (
                list(self.acquire_holidays_dict(recent_work_count).values())[-1 + i]
                if self.in_day.month in [4, 10]
                else list(self.acquire_holidays_dict(recent_work_count).values())[
                    -2 + i
                ]
            )

        return next_holiday

    def _find_matching_holiday_date(
        self, acquisition_date: date, holiday_dict: OrderedDict[date, int]
    ) -> date:
        """
        付与日に相当する年休付与日を探す

        @Param
            acquisition_date: date これが付与日と一致する
            holiday_dict: OrderedDict[date, int] 年休付与辞書
        @Return
            : date 一致する日付（見つからない場合はNone）
        """
        matched_date = None
        # min_diff = float("inf")
        # saved_date = None

        for i, holiday_date in enumerate(holiday_dict.keys()):
            holiday_date_normalized = (
                holiday_date.date() if hasattr(holiday_date, "date") else holiday_date
            )
            # diff = abs((holiday_date_normalized - acqisition_date).days)
            # print(f"Diff: {acquisition_date}, {holiday_date_normalized}")
            # 一致する場合（4月、10月）
            if holiday_date_normalized == acquisition_date:
                matched_date = holiday_date

            # 一致しない場合（4月、10月以外）は、下記の手法で
            # len(acquisition_dates) == 4 対応
            # get_effective_holidaysのifが一個減った
            if isinstance(holiday_date, datetime):
                pass
            elif acquisition_date > holiday_date_normalized:
                matched_date = holiday_date_normalized
            # len(acquisition_dates) == 4 対応
            # matched_dateのNoneの i == 1 になるところ、逆の条件の値が必要になる
            elif matched_date is None and acquisition_date < holiday_date_normalized:
                matched_date = holiday_date_normalized
            # 上記elifと同様
            # elif i == 1:  # and acquisition_date < holiday_date_normalized:
            #     saved_date = holiday_date_normalized
            #     matched_date = saved_date
            # print(f"_matched date: {matched_date}")

            # made by Cursor
            # elif diff < min_diff:
            #     min_diff = diff
            #     print(f"Min diff: {min_diff}")
            #     matched_date = holiday_date_normalized
        return matched_date

    def _process_acquisition_period(
        self, acquisition_date: date, work_count: int
    ) -> int:
        """
        単一の付与期間の年休日数を処理する

        @Param
            acquisition_date: date 付与日
            work_count: int 勤務日数
        @Return
            : int 年休日数
        """
        holiday_dict = self.acquire_holidays_dict(work_count)
        print(f"Process holiday dict: {holiday_dict}")

        # 一致する日付を探す
        matched_date = self._find_matching_holiday_date(acquisition_date, holiday_dict)
        print(f"Matched date: {matched_date}")

        if matched_date:
            return holiday_dict[matched_date]
        else:
            # デフォルト値を設定（ログ出力）
            logger = HolidayLogger.get_logger("WARNING", "-info")
            logger.warning(
                f"ID{self.id}: 付与日 {acquisition_date} "
                f"に対応する年休日数が見つかりません。"
            )
            return 0

    def get_effective_holidays(self) -> OrderedDict[date, int]:
        """
        年休付与日と付与日数の対応関係を整理して返す

        @Return
            : OrderedDict[date, int] 付与日とその日数
        """
        # try:
        base_day = self.convert_base_day(self.in_day)
        acquisition_dates = self.get_acquisition_list(base_day)
        work_counts = self.count_workdays()

        if len(acquisition_dates) == 1:
            return self.acquire_inday_holidays()

        # 入職から4期間以内の場合は、最初の期間の勤務日数を12ヶ月換算する
        if len(acquisition_dates) <= 4:
            half_year_count = self.count_workday_half_year(work_counts[0])
            work_counts[0] = half_year_count

        effective_holidays = OrderedDict()
        inday_dict = self.acquire_inday_holidays()

        # 各期間の勤務日数に対応する年休付与日数を取得
        for period_index, work_count in enumerate(work_counts):
            # 現在の期間に対応する付与日を取得
            acquisition_date_index = 4 - period_index
            if len(acquisition_dates) >= 4:
                print("△Effective holidays: 入職から4期間以上")
                acquisition_date = acquisition_dates[-acquisition_date_index]
            # 当テストのモックにより、アイテムが4つになることがある
            elif len(acquisition_dates) == 3:
                print("▲Effective holidays: 入職から3期間")
                effective_holidays = inday_dict
                acquisition_date = acquisition_dates[-(acquisition_date_index) + 1]
            elif len(acquisition_dates) == 2:
                print("■Effective holidays: 入職から2期間")
                effective_holidays = inday_dict
                acquisition_date = acquisition_dates[-2]

            # 年休日数を取得
            holiday_days = self._process_acquisition_period(
                acquisition_date, work_count
            )
            effective_holidays[acquisition_date] = holiday_days

            # logger = HolidayLogger.get_logger("INFO", "-info")
            # logger.info(f"ID{self.id}: 有効な年休付与: {dict(effective_holidays)}")
        return effective_holidays

        # エラーハンドリング by Cursor、今はいらないと思う
        # except Exception as e:
        #     logger = HolidayLogger.get_logger("ERROR", "-err")
        #     logger.error(
        #         f"ID{self.id}: get_effective_holidaysでエラーが発生: {e}",
        #         exc_info=True,
        #     )
        #     return OrderedDict()


@dataclass
class HolidayCountFactory:
    _instances: Dict[int, "HolidayDayCount"] = field(default_factory=dict)

    def get_instance(self, staff_id: int) -> "HolidayDayCount":
        if staff_id not in self._instances:
            self._instances[staff_id] = HolidayDayCount(staff_id)
        return self._instances[staff_id]
