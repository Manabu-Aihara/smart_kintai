import enum
from typing import Optional


class WorkdayType(enum.Enum):
    # A = 217
    B = range(169, 217)
    C = range(121, 169)
    D = range(73, 121)
    E = range(48, 73)

    @classmethod
    def name(cls, name: str) -> str:
        return cls._member_map_[name]


# 出勤日数から、付与タイプを導く
def divide_acquire_type(count: int) -> Optional[str]:
    for char in ["B", "C", "D", "E"]:
        if count in list(WorkdayType.name(char).value):
            print(f"Acquisition type divide: {char}")
            return char
        elif count >= 217:
            char = "A"
            print(f"Acquisition type divide: {char}")
            return char
        elif count < 48:
            # raise KeyError(f" 勤務日数 {count} に対する、付与タイプが見つかりません。")
            print("Acquisition type divide: F")
            return None


# コンストラクタを作って、その引数に、各項目に与えた値の
# 1つめ、2つめ、3つめが何を意味しているか名前を与えて、
# インスタンス変数に格納して上げると、特にインスタンスを作らなくても、
# アクセス出来るようになります。
# https://note.com/yucco72/n/ne69ea7fb26e7
class AcquisitionType(enum.Enum):
    A = (list(range(10, 12)) + list(range(12, 20, 2)), 20)  # 以降20 年間勤務日数>=217
    # A = ([10, 11, 12, 14, 16, 18], 20)  # 以降20 年間勤務日数>=217
    B = ([7, 8, 9, 10, 12, 13], 15)  # 以降15 年間勤務日数range(169, 216)
    C = ([5, 6, 6, 8, 9, 10], 11)  # 以降11 年間勤務日数range(121, 168)
    D = ([3, 4, 4, 5, 6, 6], 7)  # 以降7 年間勤務日数range(73, 120)
    E = ([1, 2, 2, 2, 3, 3], 3)  # 以降3 年間勤務日数range(48, 72)
    F = ([0, 0, 0, 0, 0, 0], 0)

    def __init__(self, under5y: list, onward: int):
        super().__init__()
        self.under5y = under5y
        self.onward = onward

    # 例: AからAcquisition.Aを引き出す
    @classmethod
    def name(cls, name: Optional[str]) -> str:
        """
        Subject: 該当ID抽出に発生すると思われる例外①
        """
        if name is None:
            # raise KeyError("勤務日数に対する、付与タイプが見つかりません。")
            return cls.F
        else:
            # print(
            #     f"Enum summary: {cls._member_map_[name]}{type(cls._member_map_[name])}"
            # )
            return cls._member_map_[name]
