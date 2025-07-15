from dataclasses import dataclass, field
from typing import List, Union, Tuple


@dataclass
class AttendanceValidate:
    start_time: str
    end_time: str
    notification: str
    notification_pm: str
    # current_date: str = field(default=datetime.today().strftime("%Y年%m月%d日"))
    current_date: str
    # 午前のみの申請
    n_list: List[str] = field(
        default_factory=lambda: ["3", "5", "8", "17", "18", "19", "20"]
    )
    # 午後と共通
    n_in_common: List[str] = field(default_factory=lambda: ["4", "6", "9", "16"])
    # 時間休
    n_rest_list: List[str] = field(
        default_factory=lambda: ["10", "11", "12", "13", "14", "15", "16"]
    )
    success_message: str = field(default="保存しました。")
    uncorrect_message: str = field(default="日の勤務時間を正しく入力してください。")
    claim_message: str = field(default="日について、届出を入力しなおしてください。")

    def request_notification_type(self) -> Union[str, bool]:
        print(
            f"△Debug: notification={self.notification}, notification_pm={self.notification_pm}"
        )
        # まず、午前と午後が同じ状態の場合は無条件で False
        # ここでは「両方空文字列かつ両方時間休はTrue」と解釈します。
        if self.notification == "" and self.notification_pm == "":
            print("△Pass 1")
            return "input"
        elif (
            self.notification in self.n_rest_list
            and self.notification_pm in self.n_rest_list
        ):
            print("△Pass 1.5")
            return "input"

        if self.notification == self.notification_pm:
            print("△Pass 2")
            return False

        # 1. notification == "早退" かつ全日申請 notification_pm == "" の場合のみ True
        if self.notification == "2" and self.notification_pm == "":
            print("△Pass 2.5")
            return "input"
        elif self.notification in self.n_list + ["9"]:
            print("△Pass 3 (empty)")
            return "empty"

        if (self.notification == "4" and self.notification_pm == "6") or (
            self.notification == "6" and self.notification_pm == "4"
        ):
            print("△Pass 4 (empty)")
            return "empty"

        """
            既に "notification_am == notification_pm" の False 条件と
            "notification == "早退" かつ全日申請 and notification_pm == "" の True 条件を処理済み
        """
        #    notification == "1" or notification in n_in_common の場合は input
        #    notification == "" の場合は input
        #    notification_pm == "2" or notification_pm in n_in_common の場合は input
        #    つまり、以下の条件を満たす場合は input を返す
        #    1. notification == "1" or notification in n_in_common or notification == ""
        #    2. notification_pm == "2" or notification_pm in n_in_common or notification_pm == ""
        #    つまり、以下の条件を満たす場合
        if (
            self.notification == "1"
            or self.notification in self.n_in_common
            or self.notification == ""
        ) and (
            self.notification_pm == "2"
            or self.notification_pm in self.n_in_common
            or self.notification_pm == ""
        ):
            return "input"

        # その他の場合は False
        print(
            f"△Debug: Returning False for notification={self.notification}, "
            f"notification_pm={self.notification_pm}"
        )
        return False

    def check_input_time(self, request_phrase: Union[str, bool]) -> Tuple[str, str]:
        print(f"△Debug: request_phrase={request_phrase}, start_time={self.start_time}")
        # print(f"△Debug: request_phrase type: {type(request_phrase)}")
        # print(f"△Debug: request_phrase repr: {repr(request_phrase)}")
        # print(f"△Debug: request_phrase == 'input': {request_phrase == 'input'}")
        # print(f"△Debug: start_time == '00:00': {self.start_time == '00:00'}")
        # print(f"△Debug: request_phrase == 'empty': {request_phrase == 'empty'}")
        # print(f"△Debug: start_time != '00:00': {self.start_time != '00:00'}")

        condition1 = request_phrase == "input" and self.start_time == "00:00"
        condition2 = request_phrase == "empty" and self.start_time != "00:00"
        print(f"△Debug: condition1 (input and 00:00): {condition1}")
        print(f"△Debug: condition2 (empty and not 00:00): {condition2}")
        # print(
        #     f"△Debug: final condition (condition1 or condition2): "
        #     f"{condition1 or condition2}"
        # )

        print("△Debug: About to check if conditions...")
        if (request_phrase == "input" and self.start_time == "00:00") or (
            request_phrase == "empty" and self.start_time != "00:00"
        ):
            print(f"△Uncorrect: {self.start_time}")
            return self.uncorrect_message, "uncorrect"
        elif request_phrase is False:
            print("△Claim")
            return self.claim_message, "warning"
        else:
            print("△Success")
            return self.success_message, "success"

    def validate_attendance(self) -> Tuple[str, str]:
        if self.start_time != "00:00" and self.end_time == "00:00":
            return (
                "日について一時的に" + self.success_message,
                "pre-success",
            )
        elif self.start_time != "00:00" and self.start_time >= self.end_time:
            print("△Pass 5")
            return self.uncorrect_message, "warning"

        request_word = self.request_notification_type()
        print(f"△Debug: request_word from request_notification_type: {request_word}")
        return self.check_input_time(request_word)
