from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Tuple, Callable, Union

from sqlalchemy import and_

from . import db
from .database_base import session
from app.models_aprv import NotificationList, PaidHolidayLog
from .holiday_base import HolidayBase


@dataclass
class HolidayTimeApprove(HolidayBase):
    # スタッフID
    # id: int

    def __post_init__(self):
        super().__post_init__()

    """
    メソッド名の目安
    acquire: 日数
    get: 日付
    """
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
            session.query(
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
            session.query(PaidHolidayLog.REMAIN_TIMES)
            .filter(self.id == PaidHolidayLog.STAFFID)
            .order_by(PaidHolidayLog.id.desc())
            .first()
        )
        if last_remain is None:
            raise TypeError("まだ年休付与はありません。")
        else:
            return last_remain.REMAIN_TIMES
