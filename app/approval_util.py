from datetime import datetime
from dataclasses import dataclass
from typing import TypeVar, List, Callable, Union

from sqlalchemy import or_


T = TypeVar("T")
# table: T


@dataclass
class NoZeroTable:
    table: T
    # args: list[datetime] = field(default_factory=list)

    """
    00:00:00が存在するオブジェクトを抽出
    Param:
        table: T (クラステーブル)
        *args: str (00：00：00を持つであろう属性名)
    Return:
        datetime_query: List[T]
    """

    def select_zero_date_tables(self, *args: str) -> List[T]:
        filters = []
        for arg in args:
            filters.append(getattr(self.table, arg) == 0)

        datetime_query = self.table.query.filter(or_(*filters)).all()
        return datetime_query

    # 同日付が存在するオブジェクトを抽出
    # def select_same_date_tables(self, *args: datetime) -> List[T]:
    #     filter = getattr(self.table, args[0])==getattr(self.table, args[1])

    #     datetime_query = self.table.query.filter(and_(filter)).all()
    #     return datetime_query

    def convert_value_to_none(self, func: Callable[..., List[T]], *target: str) -> None:
        pickup_objects = func(*target)

        for pickup_obj in pickup_objects:
            for one_val in target:
                if getattr(pickup_obj, one_val).strftime("%H:%M:%S") == "00:00:00":
                    setattr(pickup_obj, one_val, None)
                    # print(f"Noneを期待：　{getattr(pickup_obj, one_val)}")
                # db.session.merge(pickup_obj)
                # db.session.commit()


def toggle_notification_type(table, arg: Union[str, int]) -> Union[int, str]:
    # 数値を内容名に置き換える
    if isinstance(arg, int):
        content_value = table.query.get(arg)
        return content_value.NAME
    # 内容名を数値に置き換える
    elif isinstance(arg, str):
        content_value = table.query.filter(table.NAME == arg).first()
        return content_value.CODE
    else:
        raise TypeError("intかstrのどちらかです")
