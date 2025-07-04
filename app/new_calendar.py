from datetime import datetime, date
import calendar
import jpholiday
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class NewCalendar:
    year: int
    month: int
    firstweekday: int = 6

    def get_monthdays_pair(self) -> List[tuple]:
        calendar_obj = calendar.Calendar()
        # firstweekdayが効かない
        twin_cals = calendar_obj.itermonthdays2(self.year, self.month)
        day_and_weeknum = []
        for twin_cal in twin_cals:
            if twin_cal[0] == 0:
                continue
            day_and_weeknum.append(twin_cal)
        return day_and_weeknum

    """
        祝祭日の日付を返す
        @Return
            : list<int>
        """

    def get_jp_holidays_num(self) -> List[int]:
        holiday_stock = []
        holidays = jpholiday.month_holidays(self.year, self.month)
        for holiday in holidays:
            holiday_stock.append(int(datetime.strftime(holiday[0], "%d")))
        return holiday_stock

    def get_weekdays(self):
        # 土日を抜く
        days_without_weekend: List[tuple] = list(
            filter(lambda d: d[1] != 5 and d[1] != 6, self.get_monthdays_pair())
        )
        # 祝日を抜く
        weekdays: List[tuple] = list(
            filter(
                lambda d: d[0] not in self.get_jp_holidays_num(), days_without_weekend
            )
        )
        return weekdays

    """
        ○日がその月の第何週か
        @Param
            : int 要求する日
        @Return
            : int
        """

    def get_nth_dow(self, day: int) -> int:
        first_dow = calendar.monthrange(self.year, self.month)[0]
        offset = (first_dow - self.firstweekday) % 7
        return (day + offset - 1) // 7 + 1

    """
        date型日付と祝日のペア
        @Return
            : list<dict<date, str | None>>
        """

    def make_calendar_table(self) -> List[Dict[date, Optional[str]]]:
        last_day_of_month: int = calendar.monthrange(self.year, self.month)[1]
        weekday_to_holiday = [
            {
                date(self.year, self.month, d): jpholiday.is_holiday_name(
                    date(self.year, self.month, d)
                )
            }
            for d in range(1, last_day_of_month + 1)
        ]
        return weekday_to_holiday
