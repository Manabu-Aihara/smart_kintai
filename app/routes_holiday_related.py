from typing import List
from datetime import datetime
import requests
import re

from flask import jsonify, make_response, render_template, request, redirect
from flask_login import current_user
from apscheduler.schedulers.background import BackgroundScheduler

from . import app
from .database_base import session
from .models import User, Team
from .carry_over_lib import config_from_to_holiday, calculate_carry_over_all
from .acquisition_holidays_lib import acquire_holidays_from_now


@app.route("/select-for-carry-over", methods=["GET", "POST"])
def select_for_carry_over():
    # ここで必要な処理を実装
    user_info = (
        session.query(User.LKANA).filter(User.STAFFID == current_user.STAFFID).first()
    )
    team_list = session.query(Team).all()

    if request.method == "POST":
        return redirect(f"/carry-over/{request.form.get('team_number')}")

    return render_template(
        "attendance/select_team_of_carry.html", user_info=user_info, team_list=team_list
    )


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
    # prev_data_url = f"http://0.0.0.0:8001/frame-prev-data/{shozoku_code}"
    try:
        two_years_data_dict = retrieve_api_data(data_url)
        # prev_data_dict = retrieve_api_data(prev_data_url)

        base_dict_result = calculate_carry_over_all(two_years_data_dict)
        # prev_dict_result = calculate_prev_carry(prev_data_dict)
        return jsonify(base_dict_result)
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500


# @app.route("/confirm-grant-holidays", methods=["GET"])
def output_acquisition_html():
    html = """
<!DOCTYPE html><html><body>
    """
    for concerned_staff, result_info_dict in acquire_holidays_from_now().items():
        html += f"<section><div>対象ID: {concerned_staff}</div>"
        html += f"<div>入職日: {result_info_dict.get('in_day')}</div>"
        html += (
            f"<div>ここ1年の勤務日数: {result_info_dict.get('recent_work_count')}</div>"
        )
        html += f"<div>次の付与日数: {result_info_dict.get('from_now_on_grant')}</div></section>"

    html += "<p>付与日数の計算は、勤務日数に基づいています。</p>"
    html += "</body></html>"
    return html


@app.route("/confirm-grant-holidays", methods=["GET"])
def confirm_grant_holidays():
    from_day, to_day = config_from_to_holiday()
    from_now_holidays = acquire_holidays_from_now()
    today = datetime.now().strftime("%Y年%m月%d日")

    return render_template(
        "attendance/confirm_grant_holidays.html",
        from_now_holidays=from_now_holidays,
        from_month=from_day.month,
        today=today,
    )
