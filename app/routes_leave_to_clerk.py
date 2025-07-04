from typing import Dict, Optional, TypeVar, List
from datetime import datetime

from flask import render_template, redirect, request
from flask.helpers import url_for
from flask_login import current_user
from flask_login.utils import login_required
from sqlalchemy import or_

from . import app, db
from .models import StaffLogin, User, Contract
from .db_check_util import check_contract_value, compare_db_item


def pulldown_select_page(
    option_value: str, current_id: Optional[int], *args_pattern: int
):
    url_dict: Dict[int, str] = {
        "0": "clerk_select_page",
        "1": "jimu_oncall_count_26",
        "2": "set_up_users_list",
        "3": "get_calc_month_table",
    }
    if option_value in ["0", "1", "2"]:
        return redirect(url_for(url_dict.get(option_value), STAFFID=current_id))
    else:
        print(f"Page args: {args_pattern[0]} {args_pattern[1]}")
        date_type_today = datetime.today()
        default_y_m = date_type_today.strftime("%Y-%m")
        return redirect(
            url_for(
                url_dict.get("3"),
                startday=args_pattern[0],
                worktype=args_pattern[1],
                selected_date=default_y_m,
            )
        )


@app.route("/clerk_select_page", methods=["GET", "POST"])
@login_required
def clerk_select_page():
    stf_login = db.session.get(StaffLogin, current_user.STAFFID)
    select_page: Dict[int, str] = {
        1: "オンコールチェック",
        2: "所属スタッフ出退勤確認",
        3: "常勤: 出退勤集計(1日～末日）",  # /1/1
        4: "パート: 出退勤集計(1日～末日）",  # /1/2
        5: "常勤: 出退勤集計(26日～25日)",  # /26/1
        6: "パート: 出退勤集計(26日～25日)",  # /26/2
    }
    newtype_flag = True

    if request.method == "POST":
        dat = request.form.get("select_page")
        if dat == "0" or dat == "1" or dat == "2":
            return pulldown_select_page(dat, current_id=current_user.STAFFID)
        elif dat == "3":
            return pulldown_select_page(dat, None, 1, 1)
        elif dat == "4":
            return pulldown_select_page(dat, None, 1, 2)
        elif dat == "5":
            return pulldown_select_page(dat, None, 26, 1)
        elif dat == "6":
            return pulldown_select_page(dat, None, 26, 2)

    return render_template(
        "attendance/jimu_select_page_diff.html",
        STAFFID=current_user.STAFFID,
        select_page=select_page,
        type_flg=newtype_flag,
        stf_login=stf_login,
    )


"""
    第2引数（退職日）が今日を過ぎていても、今月なら対象とする
    @Params:
        : list<T> models.Userを想定
        : str models.User.OUTDAYを想定
    @Return
        : list<T> models.Userを想定
    """
T = TypeVar("T")


def extract_retreat_users(
    query_instances: List[T], date_columun: str = "OUTDAY"
) -> List[T]:
    today = datetime.today()
    result_data_list = []
    for query_instance in query_instances:
        # 退職日
        date_c_name: datetime = getattr(query_instance, date_columun)
        if (
            date_c_name is None
            or date_c_name > today
            or (
                date_c_name.year == today.year
                # ここの == だね
                and date_c_name.month == today.month
            )
        ):
            result_data_list.append(query_instance)

    return result_data_list


@app.route("/users_list_page/<STAFFID>", methods=["GET", "POST"])
@login_required
def set_up_users_list(STAFFID):
    stf_login = db.session.get(StaffLogin, current_user.STAFFID)
    # STAFFIDログインしてる人
    jimu_usr = db.session.get(User, STAFFID)

    base_user_list = (
        db.session.query(
            User.STAFFID,
            User.LNAME,
            User.FNAME,
            User.OUTDAY,
            User.DISPLAY,
            Contract.NAME,
        ).join(Contract, User.CONTRACT_CODE == Contract.CONTRACT_CODE)
        # .filter(or_(User.OUTDAY == None, User.OUTDAY > datetime.today()))
        # .all()
    )

    team_user_list = base_user_list.filter(User.TEAM_CODE == jimu_usr.TEAM_CODE).all()

    all_user_list = base_user_list.all()
    disp_all_user = extract_retreat_users(all_user_list)

    """ 2024/9/2 追加分
        データベース契約形態の違い指摘部分 """
    caution_id_list = []
    exception_message = "テーブル間で、契約形態が合致していません"
    for user in all_user_list:
        unknown_value = compare_db_item(user.STAFFID, check_contract_value)
        if isinstance(unknown_value, int):
            caution_id_list.append(unknown_value)

    """ 2024/7/19 追加機能分 """
    filters194 = []
    # if STAFFID == 194:
    filters194.append(User.DEPARTMENT_CODE == jimu_usr.DEPARTMENT_CODE)
    filters194.append(User.DEPARTMENT_CODE == 7)
    reference_user_list = base_user_list.filter(or_(*filters194)).all()
    # print(f"Members: {reference_user_list}")

    today = datetime.today().strftime("%Y-%m-%d %H:%M:%S")

    this_month = datetime.today().strftime("%Y-%m")

    return render_template(
        "attendance/clerk_user_list.html",
        jimu_usr=jimu_usr,
        team_u_lst=team_user_list,
        all_u=disp_all_user,
        ref_lst=reference_user_list,
        today=today,
        this_month=this_month,
        cause_users=caution_id_list,
        exception=exception_message,
        stf_login=stf_login,
    )
