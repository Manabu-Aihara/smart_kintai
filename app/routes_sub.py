import os
from datetime import datetime
from typing import List
import re

from flask import render_template, redirect, request, jsonify, make_response, url_for

from flask_login import current_user
from flask_login.utils import login_required
from flask_cors import CORS, cross_origin

from app import app, db
from app.auth_middleware import (
    token_required,
    issue_token,
    get_user_group_id,
    get_user_group,
)
from app.models_tt import TodoOrm, EventORM
from app.models import RecordPaidHoliday, Team, User
from app.models_aprv import PaidHolidayLog
from .holiday_time_approve import HolidayTimeApprove

# 絶対こっち
origins = [
    os.getenv("CLOUD_TIMETABLE4"),
    os.getenv("CLOUD_TIMETABLE"),
    os.getenv("CLOUD_CALC_PAGE"),
    "http://localhost:5173",
]
CORS(app, supports_credentials=True, origins=origins)
# app.config.update(SESSION_COOKIE_SAMESITE="None")
# CORS(app)


@app.route("/dummy-form/<target_id>", methods=["GET"])
@login_required
def appear_sub(target_id):
    recent_todo = TodoOrm.query.order_by(TodoOrm.id.desc()).first()
    return render_template(
        "admin/dummy.html", t_num=target_id, recent=recent_todo, stf_login=current_user
    )


@app.route("/todo/all", methods=["GET"])
# @login_required
@token_required
def print_all_todo(auth_user) -> List[TodoOrm]:

    td_dict_list = []
    todo_list: list = db.session.query(TodoOrm).all()
    for todo in todo_list:
        td_dict_list.append(todo.to_dict())

    return td_dict_list


# @app.route("/redirect")
# @login_required
# def redirect_func():
#     token_dict = issue_token(current_user.STAFFID)
#     # response.headers["Authorized"] = token["data"]
#     return redirect(url_for("post_access_token", token_data=token_dict["data"]))


# def get_user_group_id() -> Tuple[int, int]:
#     print(f"Result current user: {current_user}")
#     timetable_user = (
#         db.session.query(User).filter(User.STAFFID == current_user.STAFFID).first()
#     )
#     return timetable_user.STAFFID, timetable_user.DEPARTMENT_CODE


@app.route("/timetable/auth", methods=["GET", "POST"])
@login_required
def post_access_token():
    print(f"Result current user: {current_user.STAFFID}")
    user_num, group_num = get_user_group_id(current_user.STAFFID)
    print(f"First group number: {group_num}")
    token_dict = issue_token(user_num, group_num)
    # resp = make_response(jsonify(token_data))
    return redirect(f"http://localhost:5173/auth?token={token_dict['data']}")
    # cloud_site = os.getenv("CLOUD_TIMETABLE4")
    # return redirect(f"{cloud_site}/auth?token={token_dict['data']}")


@app.route("/calc/auth", methods=["GET", "POST"])
@login_required
def post_to_token():
    user_num, group_num = get_user_group_id(current_user.STAFFID)
    token_dict = issue_token(user_num, group_num)
    return redirect(f"http://0.0.0.0:8001/users/me?token={token_dict['data']}")
    # cloud_site = os.getenv("CLOUD_CALC_PAGE")
    # return redirect(f"{cloud_site}/users/me?token={token_dict['data']}")
    # return redirect("https://hello-865742550561.asia-northeast1.run.app")


@app.route("/mcp/auth", methods=["GET", "POST"])
@login_required
def post_secure_data():
    user_num, group_num = get_user_group_id(current_user.STAFFID)
    token_dict = issue_token(user_num, group_num)
    return redirect(f"http://127.0.0.1:8001/secure-data?token={token_dict['data']}")


@app.route("/refresh", methods=["GET", "POST"])
# @login_required
@token_required
def refresh_token(auth_user, extension):
    new_token = issue_token(auth_user.STAFFID, extension)
    print(f"New token type: {type(make_response(jsonify(new_token)))}")
    print(f"New token: {new_token}")

    return new_token["data"]


@app.route("/timetable/inquiry", methods=["GET", "POST"])
# @login_required
@token_required
def print_user_inquiry(auth_user, extension):
    print(f"Auth user at server: {auth_user}")
    print(f"Group number: {extension}")
    # user_num, group_num = get_user_group_id()
    team = db.session.get(Team, extension)
    return {
        "staff_id": str(auth_user.STAFFID),
        "group_id": extension,
        "group_name": team.SHORTNAME,
    }


@app.route("/group/all", methods=["GET"])
@token_required
def get_team_events(auth_user, extension):
    events_of_team = db.session.query(EventORM).filter(Team.CODE == extension).all()
    return [event.to_dict() for event in events_of_team]


@app.route("/group/users", methods=["GET", "POST"])
@token_required
def get_team_member(auth_user, extension):
    print(f"Group code: {extension}")
    same_team_member = db.session.query(User).filter(User.TEAM_CODE == extension).all()
    return [
        {"staff_id": m.STAFFID, "family_kana": m.FKANA, "last_kana": m.LKANA}
        for m in same_team_member
    ]


@app.route("/event/all", methods=["GET"])
@token_required
def get_all_event(auth_user, extension):
    event_list = db.session.query(EventORM).all()
    return [event_item.to_dict() for event_item in event_list]
    # なぜこっちでインスタンスができない!?
    # group = Team(event_item.group_id)
    # group = db.session.get(Team, event_item.group_id)
    # print(f"Team name: {group.NAME}")

    # return event_dict_list


@app.route("/event/user", methods=["GET", "POST"])
@token_required
def get_user_event(auth_user, extension):
    user_events = (
        db.session.query(EventORM).filter(EventORM.staff_id == auth_user.STAFFID).all()
    )
    return [user_event.to_dict() for user_event in user_events]


@app.route("/group-names", methods=["GET", "POST"])
@token_required
def get_team_name(auth_user, extension):
    team_query = db.session.query(Team).all()
    return [t.SHORTNAME for t in team_query]


def convert_strToDate(str_date: str):
    regex_data = re.sub(r"\.\d{3}Z", "", str_date)
    replaced_str_data = regex_data.replace("T", " ")
    print(f"変更Time: {replaced_str_data}")
    f = "%Y-%m-%d %H:%M:%S"
    # replaced_str_data = str_date.replace("T", " ").replace(".000Z", "")
    return datetime.strptime(replaced_str_data, f)


@app.route("/event/add", methods=["POST"])
@token_required
def append_event_item(auth_user, extension):
    event_item = EventORM()
    event_item.staff_id = request.json["staff_id"]
    # extensionがrequest.json["group"]に被る？
    print(f"{extension} {request.json['group']}")
    event_item.group_id = request.json["group"]
    event_item.start_time = convert_strToDate(request.json["start_time"])
    event_item.end_time = convert_strToDate(request.json["end_time"])
    event_item.title = request.json["title"]
    db.session.add(event_item)
    db.session.commit()
    # これが絶対必要だった
    return redirect("/event/all")


@app.route("/event/update/<id>", methods=["POST"])
@token_required
def update_event_item(auth_user, extension, id: str):
    target_item = db.session.query(EventORM).filter(EventORM.id == int(id)).first()
    target_item.summary = request.json["summary"]
    target_item.progress = request.json["progress"]
    db.session.merge(target_item)
    db.session.commit()
    # これが絶対必要だった
    return redirect("/event/all")


@app.route("/event/remove/<id>", methods=["DELETE"])
@token_required
def remove_event_item(auth_user, extension, id: str):
    try:
        target_item = db.session.query(EventORM).filter(EventORM.id == int(id)).first()
        print(f"Delete: {isinstance(target_item, EventORM)}")
        db.session.delete(target_item)
        db.session.flush()
    except Exception as e:
        print(f"DB Exception: {e}")
        db.session.rollback()
    else:
        db.session.commit()
    # これが絶対必要だった
    return redirect("/event/all")


# 使わないかもAPI
@app.route("/date/update/<id>", methods=["POST"])
@token_required
def flush_date_item(auth_user, extension, id: str):
    target_item = db.session.query(EventORM).filter(EventORM.id == int(id)).first()
    target_item.start_time = request.json["start"]
    target_item.end_time = request.json["end"]
    print(f"DnD time: {target_item}")
    db.session.merge(target_item)
    db.session.flush()


@app.route("/date/update", methods=["POST"])
@token_required
def commit_date_item(auth_user, extension):
    json_data = request.json
    print(f"変更したい: {json_data['data']}")
    for dict_data in json_data["data"]:
        try:
            target_item = (
                db.session.query(EventORM)
                .filter(EventORM.id == dict_data["id"])
                .first()
            )
            # print(convert_strToDate(dict_data["start"]))
            target_item.start_time = convert_strToDate(dict_data["start"])
            target_item.end_time = convert_strToDate(dict_data["end"])
            db.session.merge(target_item)
            db.session.flush()
        except Exception as e:
            print(f"DB Exception: {e}")
            db.session.rollback()
        else:
            db.session.commit()

    return redirect("/event/all")


def get_target_user_list(base_month: str) -> List[RecordPaidHoliday]:
    holiday_info_list = db.session.query(
        RecordPaidHoliday.STAFFID, RecordPaidHoliday.WORK_TIME
    ).all()

    month_target_list = []
    for holiday_info in holiday_info_list:
        holiday_acquire_obj = HolidayTimeApprove(holiday_info.STAFFID)
        if holiday_acquire_obj.convert_base_day().month == int(base_month):
            month_target_list.append(holiday_info)

    return month_target_list


@app.route("/holidays-form/<month>", methods=["GET"])
@login_required
# @auth_approval_user
def input_holiday_remains(month):
    # 入力必要項目は、残り日数、可能なら内時間休 -> D_PAIDHOLIDAY_LOG
    remain_exist_list = []
    for target_user in get_target_user_list(month):
        holiday_acquire_obj = HolidayTimeApprove(target_user.STAFFID)
        try:
            remain_exist_list.append(
                holiday_acquire_obj.print_remains() / target_user.WORK_TIME
            )
        except TypeError as e:
            print(e)
            remain_exist_list.append("")

        input_id_zip = zip(get_target_user_list(month), remain_exist_list)

    return render_template(
        "admin/before_acquisition.html",
        month=month,
        input_id_list=list(input_id_zip),
        stf_login=current_user,
    )


@app.route("/holidays-regist/<month>", methods=["POST"])
@login_required
def regist_before_acquisition(month):
    # 必要項目は、残り日数、可能なら内時間休
    # 必須出力項目は、年休付与タイプ
    remain_day_list: List[str] = request.form.getlist("remain_days")
    # 内時間休分
    sum_time_rest_list: List[str] = request.form.getlist("time_rests")
    for i, target_user in enumerate(get_target_user_list(month)):
        if sum_time_rest_list[i] != "":
            truncate_times: int = (
                target_user.WORK_TIME
                - int(sum_time_rest_list[i]) % target_user.WORK_TIME
            )
        else:
            truncate_times = 0
            # print(sum_time_rest_list[i])

        result_remain: float = (
            float(remain_day_list[i]) * target_user.WORK_TIME
        ) - truncate_times

        one_phl_data = PaidHolidayLog(
            target_user.STAFFID,
            result_remain,
            None,
            None,
            None,
            "年休システム稼働前入力",
        )
        print(truncate_times)
        db.session.add(one_phl_data)

    db.session.commit()

    return redirect("/")
