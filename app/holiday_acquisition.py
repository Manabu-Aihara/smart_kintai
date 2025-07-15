from datetime import date, datetime, timedelta
from dataclasses import dataclass
from typing import List, Tuple, Callable, Union
from collections import OrderedDict
from monthdelta import monthmod
from dateutil.relativedelta import relativedelta

from sqlalchemy import and_

from . import db
from .models import (
    StaffHolidayContract,
    StaffJobContract,
    Contract,
    User,
    RecordPaidHoliday,
    Attendance,
)
from .models_aprv import NotificationList, PaidHolidayLog
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
class HolidayAcquire:
    # スタッフID
    id: int

    def __post_init__(self):
        target_user = db.session.query(User).filter(User.STAFFID == self.id).first()
        user_contract = (
            db.session.query(StaffJobContract)
            .filter(StaffJobContract.STAFFID == self.id)
            .order_by(StaffJobContract.START_DAY.asc())
            .first()
        )
        if target_user.INDAY is None:
            self.in_day: datetime = datetime.combine(
                user_contract.START_DAY, datetime.min.time()
            )
        elif target_user.INDAY is not None:
            #     if isinstance(target_user.INDAY, datetime):
            self.in_day = target_user.INDAY
        #     elif isinstance(target_user.INDAY, date):
        #         self.in_day = datetime.combine(target_user.INDAY, datetime.min.time())
        #     else:
        #         # エラー処理
        #         raise TypeError(f"ID{self.id}: 入職日がありません。")
        else:
            raise TypeError(f"ID{self.id}: 入職日がありません。")

        # 契約休暇時間 holiday_base_time: float
        contract_holiday_time = (
            db.session.query(StaffHolidayContract.HOLIDAY_TIME)
            .filter(StaffHolidayContract.STAFFID == self.id)
            .first()
        )
        alternate_time = (
            db.session.query(
                RecordPaidHoliday.BASETIMES_PAIDHOLIDAY,
            )
            .filter(self.id == RecordPaidHoliday.STAFFID)
            .first()
        )
        if user_contract.CONTRACT_CODE == 2:
            self.holiday_base_time = (
                contract_holiday_time.HOLIDAY_TIME
                if contract_holiday_time.HOLIDAY_TIME is not None
                else alternate_time.BASETIMES_PAIDHOLIDAY
            )
        else:
            contract_obj = db.session.get(Contract, user_contract.CONTRACT_CODE)
            self.holiday_base_time = contract_obj.WORKTIME

        if self.holiday_base_time is None:
            raise TypeError("ID{self.id}: 契約休暇時間の値がありません。")
            # with open("holiday_err.log", "a") as f:
            #     f.write(
            #         f"{self.id}: D_HOLIDAY_HOSTORY.HOLIDAY_TIME及び、M_RECORD_PAIDHOLIDAY.BASETIMES_PAIDHOLIDAYの値を確認してください。\n"
            #     )

    # 勤務形態 acquisition_key: ['A', 'B', 'C', 'D', 'E']
    def get_acquisition_key(self) -> str:
        acquisition_key = (
            db.session.query(
                RecordPaidHoliday.ACQUISITION_TYPE,
            )
            .filter(self.id == RecordPaidHoliday.STAFFID)
            .first()
        )
        return acquisition_key.ACQUISITION_TYPE

    """
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
    付与日のリストを返す
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

    # ちゃんとした付与日のリストを返すdata型で
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
    時間を日数と時間に直す表示用
    @Param
        func: Callable<, float> クラス内メソッド
    @Return
        : Tuple<int, float> 日数と時間
        """

    def convert_tuple(self, func: Callable[..., float]) -> Tuple[int, float]:
        # func()はダメ
        return func // self.holiday_base_time, func % self.holiday_base_time

    # 年休消費項目
    #     3, 4, range(10, 16)
    """
    勤務時間に応じた、申請時間を計算
    @Param
        notification_id: int
    @Return
        申請時間: float
    """

    def get_notification_rests(self, notification_id: int) -> Union[float, str]:
        # 年休対象項目ID（M_NOTIFICATION）
        n_code_list: List[int] = [3, 4, 9, 10, 11, 12, 13, 14, 15]

        # 条件フィルター
        filters = []
        filters.append(NotificationList.id == notification_id)
        filters.append(NotificationList.N_CODE.in_(n_code_list))

        # start_day, end_day, start_time, end_time = (
        notify_datetimes = (
            db.session.query(
                NotificationList.START_DAY,
                NotificationList.END_DAY,
                NotificationList.START_TIME,
                NotificationList.END_TIME,
            )
            .filter(and_(*filters))
            .first()
        )
        # 条件2番目に引っかからなかった場合
        if notify_datetimes is None:
            # 諸事情により、例外やめる
            # raise TypeError("年休に関わりのない項目です。")
            return "年休に関わりのない項目です。"

        # 申請開始日、終了日が同じ場合
        end_day = (
            notify_datetimes.START_DAY
            if notify_datetimes.END_DAY is None
            else notify_datetimes.END_DAY
        )
        """
        要注意！！
            routes_approvals::get_notification_listでは、DBから00：00：00はNoneになる
            なぜかテスト環境では発生しない:原因不明
            TypeError: combine() argument 2 must be datetime.time, not None対策
            """
        start_time = (
            datetime.min.time()
            if notify_datetimes.START_TIME is None
            else notify_datetimes.START_TIME
        )
        end_time = (
            datetime.min.time()
            if notify_datetimes.END_TIME is None
            else notify_datetimes.END_TIME
        )
        # datetime.timeのためにdatetimeに変換
        comb_start = datetime.combine(notify_datetimes.START_DAY, start_time)
        comb_end: datetime = datetime.combine(end_day, end_time)
        # 月をまたぐかもしれないので、単純に.dayで計算できない
        diff_day: timedelta = end_day - notify_datetimes.START_DAY
        # 力技でtimedeltaをfloatに
        day_side: float = diff_day.total_seconds() // (3600 * 24) + 1
        # こちらは.hourでintに変換
        hour_side = comb_end.hour - comb_start.hour
        # -もあり得る
        minute_side = comb_end.minute - comb_start.minute
        minute_side_float: float = minute_side / 60
        return (
            day_side * (hour_side if hour_side != 0 else self.holiday_base_time)
            + minute_side_float
        )

    """
    残り日数というより、時間で表記
    """

    def print_remains(self) -> float:
        last_remain = (
            db.session.query(PaidHolidayLog.REMAIN_TIMES)
            .filter(self.id == PaidHolidayLog.STAFFID)
            .order_by(PaidHolidayLog.id.desc())
            .first()
        )
        if last_remain is None:
            raise TypeError("まだ年休付与はありません。")
        else:
            return last_remain.REMAIN_TIMES

    """
    入職日＋以降の年休付与日数
    @Return
        holiday_pair: OrderedDict<date, int>
    """

    def plus_next_holidays(self) -> OrderedDict[date, int]:
        base_day = self.convert_base_day(self.in_day)
        # 入職日 + 付与リスト
        day_list = [self.in_day.date()] + self.get_acquisition_list(base_day)
        # 入職日と支給日数をリストの最初に
        holiday_pair = self.acquire_inday_holidays()

        try:
            # 入職5年くらい以内、AcquisitionType見て
            for i, acquisition_day in enumerate(
                AcquisitionType.name(self.get_acquisition_key()).under5y
            ):
                if i == len(day_list) - 1:
                    break
                else:
                    holiday_pair[day_list[i + 1]] = acquisition_day

            # 入職5年くらい以上
            if len(day_list) > len(
                AcquisitionType.name(self.get_acquisition_key()).under5y
            ):
                for day in day_list[7:]:
                    holiday_pair[day] = AcquisitionType.name(
                        self.get_acquisition_key()
                    ).onward
        except KeyError as e:
            raise e
        else:
            return holiday_pair

    """
    入職日から次回付与日までの年休付与日数を取得
    @Param
        work_count: int 勤務日数
    @Return
        holiday_pair: OrderedDict<date, int>
    """

    def acquire_holidays_dict(self, work_count: int) -> OrderedDict[date, int]:
        base_day = self.convert_base_day(self.in_day)
        day_list = [self.in_day.date()] + self.get_acquisition_list(base_day)
        holiday_pair = self.acquire_inday_holidays()

        for i, acquisition_day in enumerate(
            AcquisitionType.name(divide_acquire_type(work_count)).under5y
        ):
            if i == len(day_list) - 1:
                break
            else:
                holiday_pair[day_list[i + 1]] = acquisition_day

        return holiday_pair

    """
    2年遡っての有効時間
    @Param
        work_count: int 勤務日数
    @Return
        : float
        """

    def get_sum_holiday(self, work_count: int = 0) -> float:
        holiday_dict = (
            self.acquire_holidays_dict(work_count)
            if work_count > 0
            else self.plus_next_holidays()
        )
        print(f"ID{self.id}: 付与日数リスト: {holiday_dict}")
        holiday_list = []
        # holiday_dict.valuesは取得付与日数リスト
        for holiday in holiday_dict.values():
            holiday_list.append(holiday)

        # 2年遡っての日数（2年消滅）
        default_sum_holiday: int = (
            sum(holiday_list[-3:-1])
            if len(holiday_list) >= 3
            else sum(holiday_list[:-1])
        )

        # 総合計時間
        sum_times: float = default_sum_holiday * (self.holiday_base_time)
        return sum_times

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
    有休申請に対する、合計時間
    @Param
        time_flag: bool 時間休のみなら、True
    @Return
        : float
        """

    def sum_notify_times(self, time_flag=False) -> float:
        from_list, to_list = self.print_acquisition_data()
        filters = []
        filters.append(NotificationList.STAFFID == self.id)
        filters.append(NotificationList.START_DAY.between(from_list[-2], to_list[-2]))
        if time_flag is True:
            filters.append(PaidHolidayLog.TIME_REST_FLAG == 1)

        noification_info_list = (
            db.session.query(PaidHolidayLog.NOTIFICATION_id, NotificationList.STATUS)
            .join(PaidHolidayLog, PaidHolidayLog.NOTIFICATION_id == NotificationList.id)
            .filter(and_(*filters))
            .all()
        )

        approval_time_list = list(
            map(
                lambda x: (
                    self.get_notification_rests(x.NOTIFICATION_id)
                    if x.STATUS == 1
                    else 0
                ),
                noification_info_list,
            )
        )
        # Trueの場合、時間休だけの総合計時間
        # return noification_info_list
        return sum(approval_time_list)

    """
    出退勤による勤務日数、範囲は今回付与日から次回付与日前日
    3月、9月に起動
    """

    def count_workday(self) -> int:
        base_day = self.convert_base_day(self.in_day)
        from_list, to_list = self.print_acquisition_data()

        filters = []
        filters.append(Attendance.STAFFID == self.id)

        # 入職日年休付与以外、受けていない者（付与日リストが１個だけ）
        if (len(self.get_acquisition_list(base_day)) == 1) and (
            get_calendar_nth_dow(self.in_day.year, self.in_day.month, self.in_day.day)
            != 1
        ):
            # 入職日が第1週でなければ、翌月からカウント（今のところ私の独断）
            from_prev_last = from_list[-2] + relativedelta(months=1)
            from_prev_last = from_prev_last.replace(day=1)
        else:
            from_prev_last = from_list[-2]

        filters.append(Attendance.WORKDAY.between(from_prev_last, to_list[-2]))
        filters.append(Attendance.WORKDAY != 0)

        attendance_list = (
            db.session.query(Attendance.id)
            .join(User, User.STAFFID == Attendance.STAFFID)
            .filter(and_(*filters))
            .all()
        )

        logger = HolidayLogger.get_logger("INFO")
        logger.info(f"ID{self.id}: count: 勤務日数は{len(attendance_list)}日です。")

        return len(attendance_list)

    # 入職日年休付与以外受けていない者
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
        logger = HolidayLogger.get_logger("INFO")
        logger.info(f"ID{self.id}: {result_diff}ヶ月分を12ヶ月にしてカウントします。")

        return result_diff

    def count_workday_half_year(self) -> int:
        # UnboundLocalError – グローバル変数で回避
        # https://ann0n.com/697/
        # global workday_half_result
        # 入職月〜基準月1日前の範囲を12ヶ月分にしたもの
        workday_half_result = self.count_workday() * (12 / self.get_diff_month())
        workday_half_result = round(workday_half_result)

        logger = HolidayLogger.get_logger("INFO")
        logger.info(
            f"ID{self.id}: count_half > : 暫定勤務日数は{workday_half_result}日です。"
        )

        return workday_half_result
