# 循環参照回避
# https://ryry011.hatenablog.com/entry/2021/08/27/155026
from __future__ import annotations
from abc import ABC, abstractmethod
import datetime
from typing import TYPE_CHECKING, Optional

from app import db
from app.models import RecordPaidHoliday
from app.models_aprv import PaidHolidayLog
from app.holiday_logging import HolidayLogger

# 循環参照回避
if TYPE_CHECKING:
    from app.holiday_subject import Subject


class Observer(ABC):
    @abstractmethod
    def update(self, subject: Subject) -> None:
        raise NotImplementedError


class ObserverRegist(Observer):
    def insert_data(self, i: int, calc_data: float) -> None:
        now = datetime.datetime.now()
        add_holidays = PaidHolidayLog(
            # スタッフID
            i,
            # 付与日数（繰り越し付き）
            calc_data,
            None,
            None,
            0,
            f"{now.strftime('%Y/%m/%d')}付与分",
        )
        db.session.add(add_holidays)

    def update(self, subject: Subject) -> None:
        # notification_state: int = subject.notice_month()
        if (notification_state := subject.notice_month()) == 4 or (
            notification_state := subject.notice_month()
        ) == 10:
            print(f"Notify!---{notification_state}月年休付与の処理が入ります。---")
            for concerned_id in subject.get_concerned_staff():
                try:
                    holiday_base_time: float = subject.get_holiday_base_time(
                        concerned_id
                    )
                    result_times: float = subject.acquire_holidays(concerned_id)
                    # print(f"PAID TIMES: {concerned_id}-{result_times}")
                    self.insert_data(concerned_id, result_times)
                    db.session.flush()
                except TypeError as e:
                    print(f"ID {concerned_id}: {e}")
                    db.session.rollback()
                except Exception as e:
                    print(f"DB Exception: {e}")
                    db.session.rollback()
                else:
                    if result_times:
                        result_days = result_times / holiday_base_time
                    else:
                        result_days = 0
                    logger = HolidayLogger.get_logger("INFO", "-info")
                    logger.info(
                        f"ID{concerned_id}: {round(result_days, 1)}日付与されました。"
                    )

            # db.session.commit()


class ObserverCarry(Observer):
    def insert_carry(self, i: int, calc_data: float):
        holiday_log_data = PaidHolidayLog(
            i,
            0,
            None,
            None,
            # 繰り越し
            calc_data,
            "前回からの繰り越し",
        )
        db.session.add(holiday_log_data)

    def update(self, subject: Subject) -> None:
        # notification_state: int = subject.notice_month()
        if (notification_state := subject.notice_month()) == 3 or (
            notification_state := subject.notice_month()
        ) == 9:
            print(
                f"Notify!---{notification_state + 1}月年休付与前のチェックが入ります。---"
            )
            for concerned_id in subject.get_concerned_staff():
                try:
                    carry_times = subject.calcurate_carry_times(concerned_id)
                    # print(f"{concerned_id}: {carry_times}")
                    self.insert_carry(concerned_id, carry_times)
                    db.session.flush()
                except Exception as e:
                    print(f"DB Exception: {e}")
                    db.session.rollback()
                else:
                    logger = HolidayLogger.get_logger("INFO", "-info")
                    logger.info(f"ID{concerned_id}: {carry_times}時間繰り越しました。")

        # これが全部反映しないと、commitしないタイプ
        # db.session.commit()


class ObserverCheckType(Observer):
    def merge_type(self, i: int, past: Optional[str], post: str):
        if (past is None) or (past != post):
            r_holiday_obj = RecordPaidHoliday(i)
            r_holiday_obj.ACQUISITION_TYPE = post
            db.session.merge(r_holiday_obj)

    def update(self, subject: Subject) -> None:
        # notification_state: int = subject.notice_month()
        if (notification_state := subject.notice_month()) == 3 or (
            notification_state := subject.notice_month()
        ) == 9:
            print(
                f"Notify!---{notification_state + 1}月年休付与前のチェックが入ります。---"
            )
            for concerned_id in subject.get_concerned_staff():
                try:
                    # before_type, after_type = subject.refer_acquire_type(concerned_id)
                    # TypeError: cannot unpack non-iterable NoneType object
                    # print(before_type, after_type)
                    your_types = subject.refer_acquire_type(concerned_id)
                    # TypeError: 'NoneType' object is not subscriptable
                    print(f"observer ID{concerned_id}: {your_types[1]}")
                    self.merge_type(concerned_id, your_types[0], your_types[1])
                    db.session.flush()
                except Exception as e:
                    print(f"DB Exception: {e}")
                    db.session.rollback()
                else:
                    logger = HolidayLogger.get_logger("INFO", "-info")
                    logger.info(
                        f"ID{concerned_id}の年休付与タイプは「{your_types[1]}」です。"
                    )

            # db.session.commit()
