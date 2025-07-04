from __future__ import annotations
import enum
from typing import List, Tuple, Optional
from abc import ABC, abstractmethod
from datetime import datetime
from dateutil.relativedelta import relativedelta

from sqlalchemy import and_

from app import db
from app.models import User
from app.models_aprv import PaidHolidayLog
from app.holiday_acquisition import HolidayAcquire

from app.holiday_observer import Observer
from app.holiday_logging import HolidayLogger


class WorkdayType(enum.Enum):
    # A = 217
    B = range(169, 217)
    C = range(121, 169)
    D = range(73, 121)
    E = range(48, 73)

    @classmethod
    def name(cls, name: str) -> str:
        return cls._member_map_[name]


class Subject(ABC):
    """
    The Subject interface declares a set of methods for managing subscribers.
    """

    @abstractmethod
    def attach(self, observer: Observer) -> None:
        """
        Attach an observer to the subject.
        """
        pass

    @abstractmethod
    def detach(self, observer: Observer) -> None:
        """
        Detach an observer from the subject.
        """
        pass

    # @abstractmethod
    def notify(self) -> None:
        """
        Notify all observers about an event.
        """
        pass

    def acquire_holidays(self):
        raise NotImplementedError

    def refer_acquire_type(self):
        raise NotImplementedError

    def calcurete_carry_days(self):
        raise NotImplementedError

    def execute(self) -> None:
        raise NotImplementedError


# BASETIMES_PAIDHOLIDAY、ACQUISITION_TYPEのデコレータを使ったエラーハンドリング
def error_handler(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError as e:
            logger = HolidayLogger.get_logger("ERROR", "-err")
            # print(f"ログのIDの型: {args}-{type(args)}")
            logger.error(f"ID{args[1]}: {e}", exc_info=False)
        except ValueError as e:
            logger = HolidayLogger.get_logger("ERROR", "-err")
            logger.error(f"ID{args}: {e}", exc_info=False)
        # その他のエラー処理が必要な場合に追加できます。

    return wrapper


class SubjectImpl(Subject):
    """
    The Subject owns some important state and notifies observers when the state
    changes.
    今回起動する特定の日付の月に使用
    """

    _state: int = None
    """
    For the sake of simplicity, the Subject's state, essential to all
    subscribers, is stored in this variable.
    """

    _observers: List[Observer] = []
    """
    List of subscribers. In real life, the list of subscribers can be stored
    more comprehensively (categorized by event type, etc.).
    """

    def attach(self, observer: Observer) -> None:
        print("Subject: Attached an observer.")
        self._observers.append(observer)

    def detach(self, observer: Observer) -> None:
        print("Subject: ...Detached an observer.")
        self._observers.remove(observer)

    """
    The subscription management methods.
    """

    def notify(self) -> None:
        """
        Trigger an update in each subscriber.
        """

        print("Subject: Notifying observers...")
        for observer in self._observers:
            observer.update(self)

    # 反応する日時
    def notice_month(self) -> int:
        # Python の datetime.now で秒以下を切り捨てる方法
        # https://hawksnowlog.blogspot.com/2022/06/python-datetime-now-without-seconds.html
        now = datetime.now().replace(second=0, microsecond=0)
        it_time3 = datetime(now.year, 3, 31, 18, 0)
        it_time9 = datetime(now.year, 9, 30, 18, 0)
        it_time4 = datetime(now.year, 4, 1, 7, 0)
        it_time10 = datetime(now.year, 10, 1, 7, 0)
        self._state = 3 if (now == it_time3) else self._state
        self._state = 9 if (now == it_time9) else self._state
        self._state = 4 if (now == it_time4) else self._state
        self._state = 10 if (now == it_time10) else self._state

        # print(f"今: {now}")
        # print(f"4月1日: {it_time4}")
        return self._state

    # 対象となるスタッフを抽出、結構重要
    def get_concerned_staff(self) -> List[int]:
        concerned_id_list = []

        filters = []
        filters.append(User.INDAY != None)
        filters.append(User.OUTDAY == None)
        staff_info_list: List = (
            db.session.query(User.STAFFID, User.INDAY).filter(and_(*filters)).all()
        )

        for staff_info in staff_info_list:
            try:
                # しっかりカラム名を付ける、otherwise -> staff_id[0]
                base_day = HolidayAcquire(staff_info.STAFFID).convert_base_day(
                    staff_info.INDAY
                )
            except ValueError as e:
                logger = HolidayLogger.get_logger("ERROR", "-err")
                logger.error(f"ID{staff_info.STAFFID}: {e}", exc_info=False)
            else:
                # border_end_day: 3月31日か、9月30日
                border_end_day = base_day + relativedelta(days=-1)
                if (base_day.month == self.notice_month()) or (
                    border_end_day.month == self.notice_month()
                ):
                    concerned_id_list.append(staff_info.STAFFID)

        return concerned_id_list

    @error_handler
    def get_holiday_base_time(self, id: int) -> float:
        return HolidayAcquire(id).holiday_base_time

    """
    年休付与、4月、10月に起動
    @Param
        concerned_id: int 該当者ID
    @Return
        : float, int 総時間（繰り越し含む）
        """

    @error_handler
    def acquire_holidays(self, concerned_id: int) -> float:
        holiday_acquire_obj = HolidayAcquire(concerned_id)
        dict_data = holiday_acquire_obj.plus_next_holidays()
        dict_value = dict_data.values()
        # dict_valuesのリスト化
        acquisition_days: int = list(dict_value)[-1]

        # 繰り越し時間
        carry_times = (
            db.session.query(PaidHolidayLog.CARRY_FORWARD)
            .filter(concerned_id == PaidHolidayLog.STAFFID)
            .order_by(PaidHolidayLog.id.desc())
            .first()
        )
        # print(carry_times.CARRY_FORWARD)

        """
        重要：
        今回carry_timeのみだと…
        テーブル内データ: NULL → TypeErrorだけれども、raiseされない → (None,)だから
        テーブル内データ自体存在しない → TypeError
        raise!
            if carry_times.CARRY_FORWARD is None:
            if carry_times is None:
        """
        if carry_times is None or carry_times.CARRY_FORWARD is None:
            carry_forward_times = 0
            raise TypeError("繰り越しはありません。")
        else:
            carry_forward_times = carry_times.CARRY_FORWARD

        return (
            acquisition_days * holiday_acquire_obj.holiday_base_time
            + carry_forward_times
        )
        # return super().acquire_holidays()

    """
    出勤日数から、年休付与タイプを参照
    3月、9月に起動
    @Param
        concerned_id: int 該当者ID
    @Return
        : tuple<None | str, None | str>
        以前の付与タイプと、今回の付与タイプ
        """

    # その前に…
    # 出勤日数から、付与タイプを導く
    def divide_acquire_type(self, count: int) -> str:
        for char in ["B", "C", "D", "E"]:
            if count in list(WorkdayType.name(char).value):
                print(f"original subject divide: {char}")
                return char
            elif count >= 217:
                char = "A"
                print(f"original subject divide: {char}")
                return char
            elif count < 48:
                raise ValueError(f"original subject: 出勤日数は{count} です。")

    @error_handler
    def refer_acquire_type(
        self, concerned_id: int
    ) -> Tuple[Optional[str], Optional[str]]:

        holiday_acquire_obj = HolidayAcquire(concerned_id)
        base_day = HolidayAcquire(concerned_id).convert_base_day(
            holiday_acquire_obj.in_day
        )

        # HolidayAcquire::get_acquisition_list(base_day)[0] -> 入職日除く最初の付与日
        # if date.today() < holiday_acquire_obj.get_acquisition_list(base_day)[0]:
        # こっちの方がわかり易い
        # 要するに、付与歴から、入職日付与以外付与されてないスタッフさんかどうか
        if len(holiday_acquire_obj.get_acquisition_list(base_day)) == 1:
            sum_workday_count = holiday_acquire_obj.count_workday_half_year()
            print(f"original subject ID{concerned_id}: {sum_workday_count}")
            new_type = self.divide_acquire_type(sum_workday_count)
        else:
            sum_workday_count = holiday_acquire_obj.count_workday()
            print(f"original subject ID{concerned_id}: {sum_workday_count}")
            new_type = self.divide_acquire_type(sum_workday_count)

        print(f"結局どうなる ID{concerned_id}: {new_type}")

        """
            ここで例外を投げると、holiday_observer::merge_typeが動かない
            例外キャッチはもとより出来ない
            """
        past_type = holiday_acquire_obj.get_acquisition_key()

        return past_type, new_type

    """
        3月、9月に起動
        繰越時間の算出
        @Params: int 該当者ID
        @Return: float
        """

    @error_handler
    def calcurate_carry_times(self, concerned_id: int) -> float:
        holiday_acquire_obj = HolidayAcquire(concerned_id)

        # Trueを付けたら時間休のみの合計
        remainder = (
            holiday_acquire_obj.sum_notify_times(True)
            % holiday_acquire_obj.holiday_base_time
        )
        try:
            remain_times = holiday_acquire_obj.print_remains()
        except TypeError as e:
            print(f"{concerned_id}: {e}")
            logger = HolidayLogger.get_logger("ERROR", "-err")
            logger.error(f"ID{concerned_id}: {e}")
        else:
            # 最終残り日数を繰り越しにする
            # これは切り捨てる部分 truncate_times
            if remainder == 0:
                truncate_times = 0
            else:
                # base_time - 時間休合計の端数（時間休の合計/base_timeの余り）が切り捨て時間
                truncate_times = holiday_acquire_obj.holiday_base_time - remainder

        carry_times = remain_times - truncate_times
        return carry_times

    def execute(self) -> None:
        self.notify()
        # return super().execute()
