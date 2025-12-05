import os
import json
import re
from datetime import date
from typing import Dict, List, Tuple

from flask import request

from .routes_holiday_related import BASE_DIR


def read_alert_json(my_id: str):
    log_file_path = BASE_DIR.joinpath("logs")

    today = date.today()

    d = {}
    if today.month == 12:  # .in_([3, 9]):
        pattern = (
            r"holiday_alert_"
            # + str(today.month + 1)
            + str(10)
            + "-"
            + str(today.year)
            + r"\d{4}.json"
        )
        for filename in os.listdir(log_file_path):
            if re.search(pattern, filename):
                read_json_file = log_file_path.joinpath(filename)

        with open(read_json_file, "r") as f:
            d: Dict[str, float] = json.load(f)["alerts"]

    for k, v in d.items():
        if k == my_id:
            return v


def calc_in_alert_month() -> Tuple[str, float]:
    one_day_notifications = request.form.getlist("notifications")
    pm_notificatons = request.form.getlist("notifications_pm")
    count: float = 0.0
    half_count: float = 0.0
    time_rest_list: List[str] = ["10", "11", "12", "13", "14", "15"]
    time_rest_flag: bool = False
    for notification in one_day_notifications:
        print("Alert pass 1")
        if notification in ["3", "9"]:
            count += 1
        if notification in time_rest_list:
            print("Alert pass 1.5")
            time_rest_flag = True
    for notification_pm in pm_notificatons:
        print("Alert pass 2")
        if notification_pm in ["4", "9"]:
            half_count += 0.5
        if notification_pm in time_rest_list:
            print("Alert pass 2.5")
            time_rest_flag = True

    print(f"Add word: {time_rest_flag}")
    digestion_count = count + half_count
    additional = "以下" if time_rest_flag is True else ""

    return additional, digestion_count


# 例: holiday_to_attendance.py
def calc_in_alert_month_from_table(attd_tbl) -> Tuple[str, float]:
    time_rest_list = ["10", "11", "12", "13", "14", "15"]
    count = 0.0
    half_count = 0.0
    time_rest_flag = False

    for _, outer_value_dict in attd_tbl.items():
        for inner_value_dict in outer_value_dict.values():
            # columnsなど非日付キーをスキップ
            if not isinstance(inner_value_dict, dict):
                continue
            n = (inner_value_dict.get("notification") or "").strip()
            n_pm = (inner_value_dict.get("notification_pm") or "").strip()

            if n in ["3", "9"]:
                count += 1
            if n in time_rest_list:
                time_rest_flag = True

            if n_pm in ["4", "9"]:
                half_count += 0.5
            if n_pm in time_rest_list:
                time_rest_flag = True

    return ("以下" if time_rest_flag else ""), count + half_count
