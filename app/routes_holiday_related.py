from typing import List
import requests
import re

from flask import jsonify, make_response
from apscheduler.schedulers.background import BackgroundScheduler

from . import app
from .carry_over_lib import calculate_carry_over_all, calculate_prev_carry
from .acquisition_holidays_lib import acquire_holidays_from_now, get_concerned_members


def retrieve_api_data(url: str) -> List[dict]:
    response = requests.get(url)
    response.raise_for_status()
    api_data_dict = response.json()  # dict形式（この時点で）で取得

    result = []
    for key, item in api_data_dict.items():
        staff_id: str = re.sub(r"(\d{1,4}): (.+)", r"\1", key)
        print(f"Staff ID: {staff_id} / item: {item}")
        extracted = {
            "staff_id": int(staff_id),
            "contract_vacation_hours": item.get("契約休暇（時間）"),
            "leave_full": item.get("年休（全日）"),
            "leave_half": item.get("年休（半日）"),
            "hourly_leave": item.get("時間休"),
            "half_hour_leave": item.get("中抜け"),
        }
        result.append(extracted)

    return result


@app.route("/carry-over/<shozoku_code>", methods=["GET"])
def get_carry_over(shozoku_code):
    data_url = f"http://0.0.0.0:8001/frame-data/{shozoku_code}"
    prev_data_url = f"http://0.0.0.0:8001/frame-prev-data/{shozoku_code}"
    try:
        two_years_data_dict = retrieve_api_data(data_url)
        prev_data_dict = retrieve_api_data(prev_data_url)

        base_dict_result = calculate_carry_over_all(two_years_data_dict)
        prev_dict_result = calculate_prev_carry(prev_data_dict)
        # if base_dict_result is None:
        #     base_dict_result = {}
        # if prev_dict_result is None:
        #     prev_dict_result = {}
        return jsonify(base_dict_result)
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500


def output_html():
    for concerned_staff in get_concerned_members():
        result_info_dict = acquire_holidays_from_now(concerned_staff)
        html = "<html><body>"
        html += f"In Day: {result_info_dict.get('in_day')}<br>"
        html += f"Recent Work Count: {result_info_dict.get('recent_work_count')}<br>"
        html += f"From Now On Grant: {result_info_dict.get('from_now_on_grant')}<br>"
        html += "</body></html>"


@app.route("/confirm-grant-holidays", methods=["GET"])
def grant_holidays_appointed_day():
    scheduler = BackgroundScheduler()
    # 4月1日と10月1日に年休を付与するジョブを登録
    # scheduler.add_job(
    #     grant_paid_leave,
    #     "cron",
    #     month="4,10",
    #     day="1",
    #     hour="9",
    #     minute="0",
