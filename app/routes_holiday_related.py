import os
from typing import List
from datetime import datetime
import requests
from pathlib import Path

from flask import jsonify, render_template, request, redirect
from flask_login import current_user
from sqlalchemy import update, insert

from apscheduler.schedulers.background import BackgroundScheduler

from . import app, db
from .database_async import get_session
from .select_only_sync import read_session
from .models import User, Team
from .models_aprv import PaidHolidayLog
from .carry_over_lib import (
    config_from_to_holiday,
    retrieve_api_data,
    calculate_carry_over_all,
    fetch_api_server_dict,
    get_alert_target_dict,
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

    form_vacation_type = request.form.get("vacation_type")
    if request.method == "POST":
        return redirect(
            f"/carry-over/{request.form.get('team_number')}/{form_vacation_type}"
        )

    return render_template(
        "attendance/select_team_of_carry.html", user_info=user_info, team_list=team_list
    )


@app.route("/carry-over/<shozoku_code>/<vacation_type>", methods=["GET"])
def get_carry_over(shozoku_code, vacation_type):
    data_url = f"http://0.0.0.0:8001/frame-data/{shozoku_code}/{vacation_type}"
    # data_url = (
    #     f"{os.getenv('CLOUD_CALC_PAGE')}/frame-data/{shozoku_code}/{vacation_type}"
    # )
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
async def get_paid_holiday_list():
    paid_holiday_log_list = await get_last_paid_holiday_logs()
    return render_template(
        "attendance/paid_holiday_list_form.html",
        paid_holiday_log_list=paid_holiday_log_list,
    )


@app.route("/repair-holidays.do", methods=["POST"])
async def repair_holidays():
    update_target_list: List[int] = []
    from_now_on_grants: List[str] = []
    additional_carry_overs: List[str] = []
    # フォームからのデータを処理
    for table_id in request.form.getlist("update_target"):
        update_target_list.append(int(table_id))
        from_now_on_grants.append(request.form.get(f"from_now_on_grant_{table_id}"))
        additional_carry_overs.append(
            request.form.get(f"additional_carry_over_{table_id}")
        )

    update_paid_logs = (
        read_session.query(PaidHolidayLog)
        .filter(PaidHolidayLog.id.in_(update_target_list))
        .all()
    )

    # ここでデータベースへの保存処理などを行う
    statement_list = []
    for update_target, table_id, grant_days, carry_over in zip(
        update_paid_logs, update_target_list, from_now_on_grants, additional_carry_overs
    ):
        update_target.REMAIN_DAYS = float(grant_days)
        update_target.CARRY_FORWARD = float(carry_over)
        print(
            f"Debug: Updating ID {update_target.id} with Staff ID {update_target.STAFFID}, "
            f"Grant Days: {grant_days}, Carry Over: {carry_over}"
        )
        update_stmt = (
            update(PaidHolidayLog)
            .where(update_paid_logs.id == table_id)
            .values(update_target)
        )
        statement_list.append(update_stmt)

    async with get_session() as session:
        async with session.begin():
            for update_stmt in statement_list:
                await session.execute(statement=update_stmt)

    return redirect("/repair-holidays-form")


@app.route("/confirm-grant-holidays", methods=["GET"])
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

    return render_template(
        "attendance/confirm_grant_holidays.html",
        from_now_holidays=from_now_holidays,
        from_month=from_day.month,
        today=today,
    )


@app.route("/grant-holidays.do", methods=["POST"])
async def add_grant_holidays():
    # if request.method == "POST":
    # フォームからのデータを処理
    concerned_staff = request.form.getlist("staff_id")
    from_now_on_grant = request.form.getlist("from_now_on_grant")
    additional_carry_over = request.form.getlist("additional_carry_over")

    # ここでデータベースへの保存処理などを行う
    statement_list = []
    for staff_id, grant_days, carry_over in zip(
        concerned_staff, from_now_on_grant, additional_carry_over
    ):
        if grant_days == "":
            grant_days = 0
        if carry_over == "":
            carry_over = 0
        stmt = insert(PaidHolidayLog).values(
            STAFFID=int(staff_id),
            REMAIN_DAYS=float(grant_days),
            NOTIFICATION_id=None,
            TIME_REST_FLAG=None,
            CARRY_FORWARD=float(carry_over),
            REMARK=None,
        )
        statement_list.append(stmt)

    async with get_session() as session:
        async with session.begin():
            for stmt in statement_list:
                await session.execute(statement=stmt)

    return redirect("/repair-holidays-form")


BASE_DIR = Path(__file__).resolve().parent.parent


@app.route("/api/base-month-all/<base_month>", methods=["GET"])
def api_base_month_all(base_month: str):
    dateime_format = datetime.today().strftime("%Y%m%d")
    file_name = f"{base_month}-{dateime_format}"
    try:
        api_data_list = fetch_api_server_dict(base_month)
        # return jsonify({"data": api_data_list})
        alerts = get_alert_target_dict(api_data_list)
        # return jsonify({"alerts": alerts})
        out_path = Path(f"logs/holiday_alert_{file_name}.json")
        with out_path.open(mode="w") as f:
            # get_data(as_text=True)を使って文字列として保存...AIスゲーな
            f.write(jsonify({"alerts": alerts}).get_data(as_text=True))
        return jsonify({"alerts": alerts})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500


def excute_scheduler_alert_method():
    schedule = BackgroundScheduler()
    schedule.add_job(
        api_base_month_all, "cron", month="3, 9", day="1", hour="7", minute="0"
    )
    schedule.start()
