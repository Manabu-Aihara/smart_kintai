"""
**********
勤怠システム
2022/04版
**********
"""

import os
import datetime
from datetime import datetime, timedelta, date
from functools import wraps
from typing import List, Dict, TypeVar, Union

from flask import render_template, flash, redirect, request, session
from flask.helpers import url_for
from flask_login.utils import login_required
from flask_login import current_user
from flask import abort
from werkzeug.security import generate_password_hash

from . import app, db
from .forms import (
    AdminUserCreateForm,
    ResetPasswordForm,
    AddDataUserForm,
    SelectMonthForm,
    DisplayForm,
)
from .models import (
    User,
    Attendance,
    StaffLogin,
    Contract,
    JobType,
    RecordPaidHoliday,
    SystemInfo,
    StaffJobContract,
    StaffHolidayContract,
)
from .common_func import GetPullDownList, blankCheck
from .db_check_util import compare_db_item, check_contract_value
from .attendance_util import convert_null_role, extract_last_update

os.environ.get("SECRET_KEY") or "you-will-never-guess"
app.permanent_session_lifetime = timedelta(minutes=360)


"""***** 管理者か判断 *****"""


def admin_login_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_admin():
            return abort(403)
        return func(*args, **kwargs)

    return decorated_view


"""***** 管理者関連 *****"""


@app.route("/admin")
@login_required
@admin_login_required
def home_admin():
    form_month = SelectMonthForm()
    return render_template("admin/admin_home.html", form_month=form_month)


# ***** ユーザリストページ *****#
@app.route("/admin/users-list")
@login_required
@admin_login_required
def users_list_admin():
    stf_login = (
        db.session.query(StaffLogin)
        .filter(StaffLogin.STAFFID == current_user.STAFFID)
        .first()
    )
    login_users = db.session.query(StaffLogin).all()
    user_list = db.session.query(User).all()

    return render_template(
        "admin/users_list_admin.html",
        logins=login_users,
        users=user_list,
        stf_login=stf_login,
    )


T = TypeVar("T")
"""
    挿入データを返す
    @Params
        : int 
        : str 労働時間か休暇時間ページか
        : StaffJobContract | StaffHolidayContract 契約労働テーブルか契約休暇テーブル
    @Return 
        : list<StaffJobContract | StaffHolidayContract>
    """


def make_contract_type(
    target_staff: int,
    page_type: str = Union["1", "2"],
    contract_table: T = Union[StaffJobContract, StaffHolidayContract],
) -> List[T]:

    print(f"Page type: {page_type}")
    # HTMLのForm情報取得
    label_name_list = ["Job", "con", "Pworktime", "holiday-time", "StartDay", "EndDay"]
    form_data_dict = {}
    for l_name in label_name_list:
        form_data_dict[l_name] = request.form.getlist(l_name)

    delHistory = (
        db.session.query(contract_table)
        .filter(contract_table.STAFFID == target_staff)
        .all()
    )
    if delHistory:
        for row in delHistory:
            print(f"削除状態です: {row.STAFFID}")
            db.session.delete(row)
            db.session.flush()  # <-保留状態

    print(len(form_data_dict.get("StartDay")))  # 1つ多くなる
    data_list_to_regist = []
    # StaffJobContract, StaffHolidayContractともに存在する"StartDay"項目を選択
    for num in range(1, len(form_data_dict.get("StartDay"))):
        # print(f"!!Is it above pass?: {num}")
        # IndexError: list index out of range
        # if (
        #     form_data_dict.get("Job")[num] != ""
        #     or form_data_dict.get("con")[num] != ""
        # )
        # if page_type != "2"
        # else print(f"!!Is it below pass?: {form_data_dict.get('Job')[num]}")
        if page_type == "1":
            data_list_to_regist.append(
                contract_table(
                    target_staff,
                    form_data_dict.get("Job")[num],
                    form_data_dict.get("con")[num],
                    blankCheck(form_data_dict.get("Pworktime")[num]),
                    blankCheck(form_data_dict.get("StartDay")[num]),
                    blankCheck(form_data_dict.get("EndDay")[num]),
                )
            )
        elif page_type == "2":
            data_list_to_regist.append(
                contract_table(
                    target_staff,
                    blankCheck(form_data_dict.get("holiday-time")[num]),
                    blankCheck(form_data_dict.get("StartDay")[num]),
                    blankCheck(form_data_dict.get("EndDay")[num]),
                )
            )

    return data_list_to_regist


# ***** ユーザリストページ *****#


@app.route(
    "/admin/edit-user-history/<STAFFID>/<post_type>/<int:ProcFlag>",
    methods=["GET", "POST"],
)
@login_required
@admin_login_required
def edit_user_history(STAFFID, post_type: str, ProcFlag: int):
    stf_login = (
        db.session.query(StaffLogin)
        .filter(StaffLogin.STAFFID == current_user.STAFFID)
        .first()
    )

    # 保存ボタンが押下されたらDB登録
    if ProcFlag == 1:

        contract_states = (
            make_contract_type(STAFFID, post_type, StaffJobContract)
            if post_type != "2"
            else make_contract_type(STAFFID, post_type, StaffHolidayContract)
        )
        for state in contract_states:
            print(f"保存するもの: {state}")
            db.session.add(state)

        db.session.commit()

        dt_now = datetime.now()
        flash("保存しました。time[" + str(dt_now) + "]", "success")

    contract_info = (
        db.session.query(StaffJobContract).filter(StaffJobContract.STAFFID == STAFFID)
        if post_type != "2"
        else db.session.query(StaffHolidayContract).filter(
            StaffHolidayContract.STAFFID == STAFFID
        )
    )

    ListJob = GetPullDownList(
        JobType, JobType.JOBTYPE_CODE, JobType.NAME, JobType.JOBTYPE_CODE
    )
    ListCon = GetPullDownList(
        Contract,
        Contract.CONTRACT_CODE,
        Contract.NAME,
        Contract.CONTRACT_CODE,
    )
    StaffInfo = (
        db.session.query(StaffLogin).filter(StaffLogin.STAFFID == STAFFID).first()
    )

    # 今後の、表示・非表示の注文がありそう
    # display = "display: table-cell" if post_type != "2" else "display: none"
    # print(display)
    # protect = "" if post_type != "2" else "readonly"
    # protect_style = "" if post_type != "2" else "background-color: gray"

    return render_template(
        "admin/user_history_edit_diff.html",
        History=contract_info,
        StaffInfo=StaffInfo,
        stf_login=stf_login,
        ListJob=ListJob,
        ListCon=ListCon,
        post_type=post_type,
        # disp=display,
        # protect=protect,
        # protect_s=protect_style,
    )


# ***** ユーザ登録ページ *****#
@app.route("/admin/create-user", methods=["GET", "POST"])
@login_required
@admin_login_required
def user_create_admin():
    stf_login = (
        db.session.query(StaffLogin)
        .filter(StaffLogin.STAFFID == current_user.STAFFID)
        .first()
    )
    mes = None
    form = AdminUserCreateForm()
    if form.validate_on_submit():
        STAFFID = form.staffid.data
        PASSWORD = form.password.data
        ADMIN = form.admin.data
        existing_username = (
            db.session.query(StaffLogin).filter_by(STAFFID=STAFFID).first()
        )
        if existing_username:
            mes = "この社員番号は既に存在します。"
            flash("この社員番号は既に存在します。", "warning")

            return render_template("admin/user-create-admin.html", form=form, mes=mes)
        stl = StaffLogin(STAFFID, PASSWORD, ADMIN)
        usr = User(STAFFID)
        usr.DISPLAY = 0
        rp_holiday = RecordPaidHoliday(STAFFID=STAFFID)
        sys_info = SystemInfo(STAFFID=STAFFID)

        db.session.add(rp_holiday)
        db.session.add(sys_info)
        db.session.add(stl)
        db.session.add(usr)
        db.session.commit()
        flash("続いて、追加のユーザデータを作成します", "info")

        return redirect(url_for("edit_data_user", STAFFID=STAFFID, intFlg=0))

    if form.errors:
        flash(form.errors, "danger")

    return render_template(
        "admin/user_create_admin.html", form=form, mes=mes, stf_login=stf_login
    )


"""
    DBから役職など5項目、dictのlistで返す
    @Return:
        list<dict<str, str>>
        """


def get_role_context(db_obj) -> Dict[str, str]:
    conv_db_obj = convert_null_role(db_obj)

    return {
        "staff_id": db_obj.STAFFID,
        "department": conv_db_obj.department,
        "team": conv_db_obj.team,
        "contract": conv_db_obj.contract,
        "job_type": conv_db_obj.job_type,
        "post": conv_db_obj.post,
    }


# ***** ユーザ編集（リスト）ページ *****#
@app.route("/admin/edit-list-user", methods=["GET", "POST"])
@login_required
@admin_login_required
def edit_list_user():
    stf_login = (
        db.session.query(StaffLogin)
        .filter(StaffLogin.STAFFID == current_user.STAFFID)
        .first()
    )

    """ 2024/7/23 修正分 """
    user_infos = db.session.query(User).all()
    # user_infos = (
    #     db.session.query(User, StaffJobContract.JOBTYPE_CODE, StaffJobContract.CONTRACT_CODE)
    #     .outerjoin(StaffJobContract, StaffJobContract.STAFFID == User.STAFFID)
    #     .filter(or_(User.OUTDAY == None, User.OUTDAY > datetime.today()))
    #     .all()
    # )

    user_complete_list = []
    """ 24/9/2 追加機能 """
    caution_id_list: List[int] = []
    exception_message = "テーブル間で、契約形態及び職種が合致していません"
    # for user_info, JOBTYPE_CODE, contract_code in user_infos:
    for user_info in user_infos:
        # compare_db_item(user_info.STAFFID)
        user_necessary_dict = {
            "family_name": user_info.LNAME,
            "first_name": user_info.FNAME,
            "family_kana": user_info.LKANA,
            "first_kana": user_info.FKANA,
            # 24/9/3 それに伴う変更🙅同一人物、複数出るから
            # "job_type": get_user_role(
            #     JobType.SHORTNAME, JobType.JOBTYPE_CODE, JOBTYPE_CODE
            # ),
            # "contract": get_user_role(
            #     Contract.NAME, Contract.CONTRACT_CODE, contract_code
            # ),
            "inday": user_info.INDAY,
            "outday": user_info.OUTDAY,
            "display": user_info.DISPLAY,
        }
        user_necessary_info = dict(**user_necessary_dict, **get_role_context(user_info))
        user_complete_list.append(user_necessary_info)

        unknown_value = compare_db_item(user_info.STAFFID, check_contract_value)
        if isinstance(unknown_value, int):
            caution_id_list.append(unknown_value)

    # print(user_complete_list)
    today = datetime.today().strftime("%Y-%m-%d %H:%M:%S")

    """ ここまで """

    # if request.method == "POST":
    #     return redirect(url_for("edit_data_user", STAFFID=STAFFID))

    return render_template(
        "admin/edit_list_user.html",
        info_list=user_complete_list,
        today=today,
        cause_users=caution_id_list,
        exception=exception_message,
        stf_login=stf_login,
        # intFlg=1,
    )


# ***** ユーザ編集ページ *****#
@app.route("/admin/edit-data-user/<STAFFID>/<int:intFlg>", methods=["GET", "POST"])
@login_required
@admin_login_required
def edit_data_user(STAFFID, intFlg):
    stf_login = (
        db.session.query(StaffLogin)
        .filter(StaffLogin.STAFFID == current_user.STAFFID)
        .first()
    )
    form = AddDataUserForm()
    target_user = db.session.get(User, STAFFID)
    rp_holiday = db.session.get(RecordPaidHoliday, STAFFID)
    sys_info = db.session.get(SystemInfo, STAFFID)
    display_form = DisplayForm()

    # print(f"Form detail: {form.__dict__}")
    if form.validate_on_submit():
        if form.department.data == 0:
            DEPARTMENT_CODE = 0
        else:
            DEPARTMENT_CODE = form.department.data

        if form.team.data == 0:
            TEAM_CODE = 0
        else:
            TEAM_CODE = form.team.data

        if form.contract.data == 0:
            CONTRACT_CODE = 0
        else:
            CONTRACT_CODE = form.contract.data

        if form.job_type.data == 0:
            JOBTYPE_CODE = 0
        else:
            JOBTYPE_CODE = form.job_type.data

        if form.post_code.data == 0:
            POST_CODE = 0
        else:
            POST_CODE = form.post_code.data

        if form.worker_time.data == "" or form.worker_time.data == None:
            WORKER_TIME = int("0")
        else:
            WORKER_TIME = int(form.worker_time.data)

        if (
            form.basetime_paidholiday.data == ""
            or form.basetime_paidholiday.data == None
        ):
            BASETIMES_PAIDHOLIDAY = float("0")
        else:
            BASETIMES_PAIDHOLIDAY = float(form.basetime_paidholiday.data)

        if form.last_carriedover.data == "" or form.last_carriedover.data == None:
            LAST_CARRIEDOVER = float("0")
        else:
            LAST_CARRIEDOVER = float(form.last_carriedover.data)

        if form.social.data == 0:
            SOCIAL_INSURANCE = 0
        else:
            SOCIAL_INSURANCE = form.social.data

        if form.employee.data == 0:
            EMPLOYMENT_INSURANCE = 0
        else:
            EMPLOYMENT_INSURANCE = form.employee.data
        EXPERIENCE = form.experi.data
        TABLET = form.tablet.data
        SINGLE = form.single.data
        SUPPORT = form.support.data
        HOUSE = form.house.data
        DISTANCE = form.distance.data
        LNAME = form.lname.data
        FNAME = form.fname.data
        LKANA = form.lkana.data
        FKANA = form.fkana.data
        POST = form.post.data
        ADRESS1 = form.adress1.data
        ADRESS2 = form.adress2.data
        TEL1 = form.tel1.data
        TEL2 = form.tel2.data
        BIRTHDAY = form.birthday.data
        INDAY = form.inday.data

        OUTDAY = form.outday.data
        STANDDAY = form.standday.data

        WORKER_TIME = form.worker_time.data
        BASETIMES_PAIDHOLIDAY = form.basetime_paidholiday.data

        REMARK = form.remark.data
        MAIL = form.m_a.data
        MAIL_PASS = form.ml_p.data
        MICRO_PASS = form.ms_p.data
        PAY_PASS = form.p_p.data
        KANAMIC_PASS = form.k_p.data
        ZOOM_PASS = form.z_p.data

        target_user.DEPARTMENT_CODE = DEPARTMENT_CODE
        target_user.TEAM_CODE = TEAM_CODE
        target_user.CONTRACT_CODE = CONTRACT_CODE
        target_user.JOBTYPE_CODE = JOBTYPE_CODE
        target_user.POST_CODE = POST_CODE
        target_user.LNAME = LNAME
        target_user.FNAME = FNAME
        target_user.LKANA = LKANA
        target_user.FKANA = FKANA
        target_user.POST = POST
        target_user.ADRESS1 = ADRESS1
        target_user.ADRESS2 = ADRESS2
        target_user.TEL1 = TEL1
        target_user.TEL2 = TEL2
        target_user.BIRTHDAY = BIRTHDAY
        target_user.INDAY = INDAY
        target_user.OUTDAY = OUTDAY
        target_user.STANDDAY = STANDDAY
        target_user.SOCIAL_INSURANCE = SOCIAL_INSURANCE
        target_user.EMPLOYMENT_INSURANCE = EMPLOYMENT_INSURANCE
        target_user.EMPLOYMENT_INSURANCE = EMPLOYMENT_INSURANCE
        target_user.EXPERIENCE = EXPERIENCE
        target_user.TABLET = TABLET
        target_user.SINGLE = SINGLE
        target_user.SUPPORT = SUPPORT
        target_user.HOUSE = HOUSE
        target_user.DISTANCE = DISTANCE
        target_user.REMARK = REMARK
        """ 24/9/12 追加 """
        print(f"Check: {display_form.display.data}")
        target_user.DISPLAY = display_form.display.data
        db.session.commit()

        rp_holiday.DEPARTMENT_CODE = DEPARTMENT_CODE
        rp_holiday.LNAME = LNAME
        rp_holiday.FNAME = FNAME
        rp_holiday.LKANA = LKANA
        rp_holiday.FKANA = FKANA
        rp_holiday.INDAY = INDAY
        # OUTDAYはM_RemainPaidHolidayにはない
        rp_holiday.TEAM_CODE = TEAM_CODE
        rp_holiday.CONTRACT_CODE = CONTRACT_CODE
        rp_holiday.DUMP_REFLESH = 0
        rp_holiday.DUMP_REFLESH_CHECK = 0

        rp_holiday.WORK_TIME = WORKER_TIME
        rp_holiday.BASETIMES_PAIDHOLIDAY = BASETIMES_PAIDHOLIDAY
        rp_holiday.LAST_CARRIEDOVER = LAST_CARRIEDOVER

        db.session.commit()

        sys_info.MAIL = MAIL
        sys_info.MAIL_PASS = MAIL_PASS
        sys_info.MICRO_PASS = MICRO_PASS
        sys_info.PAY_PASS = PAY_PASS
        sys_info.KANAMIC_PASS = KANAMIC_PASS
        sys_info.ZOOM_PASS = ZOOM_PASS
        db.session.commit()

        flash("ユーザ情報を編集しました", "info")
        return redirect(url_for("edit_list_user"))

    elif intFlg == 1:

        form.department.data = target_user.DEPARTMENT_CODE
        form.team.data = target_user.TEAM_CODE
        form.contract.data = target_user.CONTRACT_CODE
        form.job_type.data = target_user.JOBTYPE_CODE
        form.post_code.data = target_user.POST_CODE
        form.lname.data = target_user.LNAME
        form.fname.data = target_user.FNAME
        form.lkana.data = target_user.LKANA
        form.fkana.data = target_user.FKANA
        form.post.data = target_user.POST
        form.adress1.data = target_user.ADRESS1
        form.adress2.data = target_user.ADRESS2
        form.tel1.data = target_user.TEL1
        form.tel2.data = target_user.TEL2
        form.birthday.data = target_user.BIRTHDAY
        form.inday.data = target_user.INDAY
        form.outday.data = target_user.OUTDAY
        form.standday.data = target_user.STANDDAY
        form.remark.data = target_user.REMARK
        form.m_a.data = sys_info.MAIL
        form.ml_p.data = sys_info.MAIL_PASS
        form.ms_p.data = sys_info.MICRO_PASS
        form.p_p.data = sys_info.PAY_PASS
        form.k_p.data = sys_info.KANAMIC_PASS
        form.z_p.data = sys_info.ZOOM_PASS
        form.worker_time.data = rp_holiday.WORK_TIME
        form.basetime_paidholiday.data = rp_holiday.BASETIMES_PAIDHOLIDAY
        form.last_carriedover.data = rp_holiday.LAST_CARRIEDOVER

        if target_user.SOCIAL_INSURANCE == 0:
            form.social.data = 0
        else:
            form.social.data = 1

        if target_user.EMPLOYMENT_INSURANCE == 0:
            form.employee.data = 0
        else:
            form.employee.data = 1

        if target_user.EXPERIENCE == 0 or target_user.EXPERIENCE is None:
            form.experi.data = 0
        else:
            form.experi.data = target_user.EXPERIENCE

        if target_user.TABLET == 0 or target_user.TABLET is None:
            form.tablet.data = 0
        else:
            form.tablet.data = target_user.TABLET

        if target_user.SINGLE == 0 or target_user.SINGLE is None:
            form.single.data = 0
        else:
            form.single.data = target_user.SINGLE

        if target_user.SUPPORT == 0 or target_user.SUPPORT is None:
            form.support.data = 0
        else:
            form.support.data = target_user.SUPPORT

        if target_user.HOUSE == 0 or target_user.HOUSE is None:
            form.house.data = 0
        else:
            form.house.data = target_user.HOUSE

        form.distance.data = target_user.DISTANCE
        """ 24/9/12 追加 """
        display_form.display.data = target_user.DISPLAY

    if form.errors:
        flash(form.errors, "danger")

    return render_template(
        "admin/edit_data_user_diff.html",
        form=form,
        disp_form=display_form,
        STAFFID=STAFFID,
        u=target_user,
        stf_login=stf_login,
        intFlg=intFlg,
    )


@app.route("/admin/delete-user/<STAFFID>", methods=["POST"])
@login_required
@admin_login_required
def user_delete_admin(STAFFID):

    # Attendances = Attendance.query.filter_by(STAFFID=STAFFID).all()
    user_login = (
        db.session.query(StaffLogin).filter(StaffLogin.STAFFID == STAFFID).first()
    )
    user_holiday_info = (
        db.session.query(RecordPaidHoliday)
        .filter(RecordPaidHoliday.STAFFID == STAFFID)
        .first()
    )
    user_system_info = (
        db.session.query(SystemInfo).filter(SystemInfo.STAFFID == STAFFID).first()
    )
    user_info = db.session.query(User).filter(User.STAFFID == STAFFID).first()

    db.session.delete(user_info)
    db.session.delete(user_system_info)
    db.session.delete(user_holiday_info)
    db.session.delete(user_login)
    db.session.commit()

    flash("ユーザを削除しました", "info")
    return redirect(url_for("home_admin"))


# ***** ユーザパスワードリセット *****#
@app.route("/admin/reset_password/<STAFFID>", methods=["GET", "POST"])
@login_required
@admin_login_required
def reset_token(STAFFID):
    stf_login = (
        db.session.query(StaffLogin)
        .filter(StaffLogin.STAFFID == current_user.STAFFID)
        .first()
    )
    STAFFID = STAFFID
    Attendances = db.session.query(Attendance).filter_by(STAFFID=STAFFID).all()
    u = db.session.get(User, STAFFID)

    hid_a = ""
    hid_b = "hidden"
    form = ResetPasswordForm()
    if form.validate_on_submit():
        STAFFID = STAFFID

        if form.PASSWORD.data != form.PASSWORD2.data:
            hid_a = "hidden"
            hid_b = ""
            return render_template(
                "attendance/reset_token.html",
                title="Reset Password",
                form=form,
                STAFFID=STAFFID,
                Attendances=Attendances,
                u=u,
                hid_a=hid_a,
                hid_b=hid_b,
            )
        elif form.PASSWORD.data == form.PASSWORD2.data:
            HASHED_PASSWORD = generate_password_hash(form.PASSWORD.data)
            ADMIN = form.ADMIN.data

            db.session.query(StaffLogin).filter_by(STAFFID=STAFFID).update(
                dict(PASSWORD_HASH=HASHED_PASSWORD, ADMIN=ADMIN)
            )
            db.session.commit()

            return redirect(url_for("indextime", STAFFID=STAFFID, intFlg=1))

    if form.errors:
        flash("エラーが発生しました。")

    return render_template(
        "admin/reset_token.html",
        title="Reset Password",
        form=form,
        STAFFID=STAFFID,
        Attendances=Attendances,
        u=u,
        hid_a=hid_a,
        hid_b=hid_b,
        stf_login=stf_login,
    )


@app.route("/select_last_change_date", methods=["POST"])
@login_required
@admin_login_required
def post_select_month():
    today = datetime.today()
    str_today = today.strftime("%Y-%m")
    select_month_value: str = str_today

    # if request.method == "POST":
    select_month_value = request.form.get("target-month")
    # print(f"Last change month: {select_month_value}")
    return redirect(f"/admin/last_save_date/{select_month_value}")


@app.route("/admin/last_save_date/<select_date>", methods=["GET"])
@login_required
@admin_login_required
def get_save_date(select_date: str):
    try:
        result_dict_list = extract_last_update(selected_date=select_date)
    except FileNotFoundError as e:
        return render_template(
            "error/exception03.html",
            title="更新された履歴がありません",
            date=select_date,
        )

    return render_template(
        "/admin/last_attend_updates.html",
        last_update_list=result_dict_list,
    )
