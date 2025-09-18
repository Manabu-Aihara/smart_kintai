from typing import List
from datetime import datetime
import requests
import re
import os

from flask import jsonify, render_template, request, redirect
from flask_login import current_user

# from apscheduler.schedulers.background import BackgroundScheduler

from . import app, db
from .models import User, Team
from .models_aprv import PaidHolidayLog
from .carry_over_lib import (
    config_from_to_holiday,
    calculate_carry_over_all,
)
from .acquisition_holidays_lib import (
    acquire_holidays_from_now,
    get_last_paid_holiday_logs,
)


@app.route("/select-for-carry-over", methods=["GET", "POST"])
def select_for_carry_over():
    # ここで必要な処理を実装
    user_info = (
        db.session.query(User.LKANA)
        .filter(User.STAFFID == current_user.STAFFID)
        .first()
    )
    team_list = db.session.query(Team).all()

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
    # data_url = f"http://0.0.0.0:8001/frame-data/{shozoku_code}"
    data_url = f"{os.getenv('CLOUD_CALC_PAGE')}/frame-data/{shozoku_code}"
    # prev_data_url = f"http://0.0.0.0:8001/frame-prev-data/{shozoku_code}"
    # prev_data_url = f"{os.getenv('CLOUD_CALC_PAGE')}/frame-prev-data/{shozoku_code}"
    try:
        two_years_data_dict = retrieve_api_data(data_url)
        # prev_data_dict = retrieve_api_data(prev_data_url)

        base_dict_result = calculate_carry_over_all(two_years_data_dict)
        # prev_dict_result = calculate_prev_carry(prev_data_dict) # prev_data_dict is commented out
        return jsonify({"base_data": base_dict_result})
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500


@app.route("/repair-holidays-form", methods=["GET"])
def get_paid_holiday_list():
    paid_holiday_log_list = get_last_paid_holiday_logs()
    return render_template(
        "attendance/paid_holiday_list_form.html",
        paid_holiday_log_list=paid_holiday_log_list,
    )


@app.route("/repair-holidays.do", methods=["POST"])
def repair_holidays():
    update_target_list = []
    from_now_on_grants = []
    additional_carry_overs = []
    # フォームからのデータを処理
    for table_id in request.form.getlist("update_target"):
        update_target_list.append(table_id)
        from_now_on_grants.append(request.form.get(f"from_now_on_grant_{table_id}"))
        additional_carry_overs.append(
            request.form.get(f"additional_carry_over_{table_id}")
        )

    update_paid_logs = db.session.query(PaidHolidayLog).filter(
        PaidHolidayLog.id.in_(update_target_list)
    )

    # ここでデータベースへの保存処理などを行う
    try:
        for update_target, grant_days, carry_over in zip(
            update_paid_logs, from_now_on_grants, additional_carry_overs
        ):
            update_target.REMAIN_DAYS = float(grant_days)
            update_target.CARRY_FORWARD = float(carry_over)
            db.session.merge(update_target)
            print(
                f"Debug: Updating ID {update_target.id} with Staff ID {update_target.STAFFID}, "
                f"Grant Days: {grant_days}, Carry Over: {carry_over}"
            )
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    finally:
        db.session.close()
    return redirect("/repair-holidays-form")


@app.route("/confirm-grant-holidays", methods=["GET", "POST"])
def confirm_grant_holidays():
    from_day, to_day = config_from_to_holiday()
    try:
        from_now_holidays = acquire_holidays_from_now()
    except TypeError as e:
        return render_template(
            "error/exception04.html",
            title="年休に関するエラー",
            exception=e,
        )
    today = datetime.now().strftime("%Y年%m月%d日")

    if request.method == "POST":
        # フォームからのデータを処理
        concerned_staff = request.form.getlist("staff_id")
        from_now_on_grant = request.form.getlist("from_now_on_grant")
        additional_carry_over = request.form.getlist("additional_carry_over")

        # ここでデータベースへの保存処理などを行う
        try:
            for staff_id, grant_days, carry_over in zip(
                concerned_staff, from_now_on_grant, additional_carry_over
            ):
                add_data = PaidHolidayLog(
                    int(staff_id),
                    float(grant_days),
                    None,
                    None,
                    float(carry_over),
                    None,
                )
                db.session.add(add_data)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        finally:
            db.session.close()
        return redirect("/repair-holidays-form")

    return render_template(
        "attendance/confirm_grant_holidays.html",
        from_now_holidays=from_now_holidays,
        from_month=from_day.month,
        today=today,
    )
