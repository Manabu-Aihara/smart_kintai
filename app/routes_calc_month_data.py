from typing import Dict, Tuple, TypeVar
import syslog
from datetime import date, datetime
import time
import cProfile
import calendar

from dateutil.relativedelta import relativedelta
from itertools import groupby

from flask import redirect, render_template, request
from flask_login import current_user
from flask_login.utils import login_required
from sqlalchemy import and_
from sqlalchemy.orm import Query
from pandas import Series

from . import app, db

# from .database_base import session
from .calc_work_classes3 import (
    CalcTimeFactory,
)
from .forms import SelectMonthForm
from .models import TableOfCount, StaffLogin, User, StaffJobContract
from .attendance_query_class import AttendanceQuery
from .attendance_util import get_month_workday, convert_null_role
from .attendance_calc import calc_attendance_of_term
from .async_db_lib import merge_count_table
from .select_only_sync import get_count_table


"""
    第2引数（退職日）が今日を過ぎていても、今月なら対象とする
    @Params:
        : Query<tuple<User, int>> AttendanceQuery.get_distinct_user_query
        : str
    @Return
        : list
    """
T = TypeVar("T")


def get_more_condition_users(
    queries: Query[Tuple[User, int]], date_column: str = "OUTDAY"
) -> list:
    today = datetime.today()
    result_query_list = []
    for query in queries:
        # 退職日
        out_day: datetime = getattr(query[0], date_column)
        if (
            out_day is None
            or out_day > today
            or (
                out_day.year == today.year
                # ここの == だね
                and out_day.month == today.month
            )
        ):
            result_query_list.append(query)

    return result_query_list


"""
    1日からカウントするか、26日からカウントするかで、期間を決定する
    @Params
        : int start_day (1 or 26)
        : int select_year
        : int select_month
    @Return
        : Tuple[date, date]
    """


def get_day_term(
    start_day: int, select_year: int, select_month: int
) -> Tuple[date, date]:
    last_day = calendar.monthrange(select_year, select_month)[1]
    if start_day != 1:
        # 1日開始以外の場合
        from_day = date(select_year, select_month, start_day) - relativedelta(
            months=1
        )  # 前月の26日
        to_day = date(select_year, select_month, 25)  # 当月の25日
    else:
        # 1日開始の場合
        from_day = date(select_year, select_month, start_day)
        to_day = date(select_year, select_month, last_day)

    return from_day, to_day


@app.route(
    "/month-calc-table/<startday>/<worktype>/<selected_date>",
    methods=["GET"],
)
@login_required
async def get_calc_month_table(startday: str, worktype: str, selected_date: str):
    # stf_login = (
    #     db.session.query(StaffLogin)
    #     .filter(StaffLogin.STAFFID == current_user.STAFFID)
    #     .first()
    # )
    form_month = SelectMonthForm()
    str_workday = "月選択をしてください。"

    # from datetime import time は不可
    # パフォーマンス測定開始
    start_time = time.perf_counter()
    c_profile = cProfile.Profile()
    c_profile.enable()

    jimu_usr = db.session.get(User, current_user.STAFFID)

    syslog.syslog(f"Select arg date: {selected_date}")
    y, m = get_month_workday(selected_date)
    y_and_m = f"{y}-{m}"

    from_day, to_day = get_day_term(int(startday), y, m)

    attendance_query_obj = AttendanceQuery(current_user.STAFFID, from_day, to_day)
    job_form: str
    if worktype == "1":
        job_form = "常勤"
        contract_distinct_user_query = (
            attendance_query_obj.get_distinct_user_query().filter(
                StaffJobContract.CONTRACT_CODE != 2
            )
        )
    elif worktype == "2":
        job_form = "パート"
        contract_distinct_user_query = (
            attendance_query_obj.get_distinct_user_query().filter(
                StaffJobContract.CONTRACT_CODE == 2
            )
        )

    if jimu_usr.TEAM_CODE != 1:
        contract_distinct_user_query = contract_distinct_user_query.filter(
            User.TEAM_CODE == jimu_usr.TEAM_CODE
        )
        # 退職者（今月を除く）を除く
        outday_conditional_users = get_more_condition_users(
            contract_distinct_user_query
        )
    else:
        outday_conditional_users = get_more_condition_users(
            contract_distinct_user_query
        )
    print(f"Distinct query length: {m}月 {len(outday_conditional_users)}")

    year_month_arg = f"{y}/{m}"

    # 今月を除く退職者を除くメンバーと
    # 永続化された集計結果
    null_checked_users = []
    count_month_list = []
    for outday_conditional_user, contract_code in outday_conditional_users:
        null_checked_users.append(convert_null_role(outday_conditional_user))
        # こちらの常勤・パート分けは、outday_conditional_userでやってる
        count_table_obj = get_count_table(
            outday_conditional_user.STAFFID, contract_code, year_month_arg
        )
        count_month_list.append(count_table_obj)

    print(f"Count query length: {m}月 {len(count_month_list)}")

    date_type_today = datetime.today()
    today = date_type_today.strftime("%Y-%m-%d %H:%M:%S")

    # c_profile.disable()
    # c_stats = pstats.Stats(c_profile)
    # c_stats.sort_stats("cumtime").print_stats(20)

    end_time = time.perf_counter()
    run_time = end_time - start_time
    pref_result = f"{today}'| 実行時間'{str(run_time)}'秒'"
    syslog.syslog(pref_result)

    return render_template(
        "attendance/calculation_month.html",
        startday=startday,
        selected_date=selected_date,
        worktype=worktype,
        form_month=form_month,
        str_workday=str_workday,
        jimu_usr=jimu_usr,
        y=y,
        m=m,
        y_and_m=y_and_m,
        FromDay=from_day,
        ToDay=to_day,
        dwl_today=date_type_today,
        job_form=job_form,
        conditional_users=null_checked_users,
        cnt_tbl_lst=count_month_list,
        today=today,
    )


def collect_calculation_attend(
    staff_id: int, from_day: date, to_day: date
) -> Dict[str, Series]:
    attendance_qry_obj = AttendanceQuery(staff_id, from_day, to_day)
    # 契約期間ごとの契約労働・休暇時間クエリー
    # attendance_queries = attendance_qry_obj.get_attendance_query()
    perfect_queries_of_person = attendance_qry_obj.get_perfect_contract_attendance()

    # groupby前にソート
    sorted_queries = sorted(
        perfect_queries_of_person,
        key=lambda x: (
            (x[1].END_DAY, x[2].END_DAY) if x[2] is not None else x[1].END_DAY
        ),
    )

    # 諸々計算クラスファクトリー
    calc_time_factory = CalcTimeFactory()
    # 結果物初期化
    calculation_dict: Dict[str, Series] = {}
    start_day_key_list = []
    loop_key_index: int = 0
    has_data = False  # データが追加されたかどうかのフラグ

    # groupby 今回契約期間ごとにSeriesで出してくれる、ユーティリティ関数
    # 注意: 値（perfect_queries_of_person）が空なら、ループすら通らない
    # 各END_DAY（個数分）をキーにする
    for index_, groups in groupby(
        sorted_queries,
        lambda x: (x[1].END_DAY, x[2].END_DAY) if x[2] is not None else x[1].END_DAY,
    ):
        has_data = True  # データが追加されたことを示す
        group_list = list(groups)

        calculation_instance = calc_time_factory.get_instance(staff_id=staff_id)
        try:
            calculation_series = calc_attendance_of_term(
                calculation_instance, group_list, staff_id
            )
        except ValueError as e:
            raise e

        # キー名は、契約期間の最終勤務日
        start_day_key_list.append(calculation_series.name)

        calculation_dict[f"{start_day_key_list[loop_key_index]}"] = calculation_series
        loop_key_index += 1

    if not has_data:  # データが追加されなかった場合
        raise TypeError(f"ID{staff_id}: 勤務実績がまだありません")
    return calculation_dict


# 再集計ボタンクリック、DB使い分けのため非同期
@app.route("/calculate-data/<startday>/<worktype>", methods=["POST"])
@login_required
async def calculate_month_data2(startday: str, worktype: str):
    form_month = SelectMonthForm()
    selected_date: str
    if form_month.validate_on_submit():
        selected_date = request.form.get("year-month")  # 選択された日付
        print(f"Select form date: {selected_date}")
        return redirect(f"/month-calc-table/{startday}/{worktype}/{selected_date}")

    print(f"Re-render date: {request.form.get('year-month')}")
    y, m = get_month_workday(request.form.get("year-month"))
    y_and_m = f"{y}/{m}"
    url_y_and_m = f"{y}-{m}"
    from_day, to_day = get_day_term(int(startday), y, m)
    print(f"From To: {from_day} {to_day}")

    attendance_query_obj = AttendanceQuery(current_user.STAFFID, from_day, to_day)
    # users_without_condition = db.session.query(User).all()
    # から変更した理由は、雇用形態が最新だから
    if worktype == "1":
        contract_distinct_user_query = (
            attendance_query_obj.get_distinct_user_query().filter(
                StaffJobContract.CONTRACT_CODE != 2
            )
        )
    elif worktype == "2":
        contract_distinct_user_query = attendance_query_obj.get_distinct_user_query().filter(
            and_(
                StaffJobContract.CONTRACT_CODE == 2,
                # 一旦ここで止まってしまうので。普段はコメントアウト
                User.STAFFID != 259,
            )
        )

    # 退職者（今月を除く）を除く
    target_users = get_more_condition_users(contract_distinct_user_query)
    for target_user, contract_code in target_users:
        try:
            calc_data_dict = collect_calculation_attend(
                target_user.STAFFID, from_day, to_day
            )
        except ValueError as e:
            return render_template(
                "error/exception04.html",
                title="集計における、必要情報の不足",
                exception=e,
            )

        for key, value in calc_data_dict.items():
            print(f"Series value work count: {value['実働日数']} {key}")
            count_table_obj = TableOfCount(target_user.STAFFID)
            making_id = (
                f"{startday}-{y_and_m}-{target_user.STAFFID}-{value['契約形態']}"
            )
        count_table_obj.id = making_id
        count_table_obj.CONTRACT_CODE = value["契約形態"]
        count_table_obj.YEAR_MONTH = y_and_m
        count_table_obj.SUM_WORKTIME = value["実働時間計"]
        count_table_obj.SUM_WORKTIME_10 = value["実働時間計（１０進法）"]
        count_table_obj.SUM_REAL_WORKTIME = value["リアル実働時間"]
        count_table_obj.WORKDAY_COUNT = value["実働日数"]
        count_table_obj.OVERTIME = value["時間外"]
        count_table_obj.OVERTIME_10 = value["時間外（１０進法）"]
        count_table_obj.HOLIDAY_WORK = value["祝日手当時間"]
        count_table_obj.HOLIDAY_WORK_10 = value["祝日手当時間（１０進法）"]
        count_table_obj.ONCALL = value["オンコール平日担当回数"]
        count_table_obj.ONCALL_HOLIDAY_ONE_DAY = value["オンコール土日（1日）担当回数"]
        count_table_obj.ONCALL_HOLIDAY_DAYTIME = value["オンコール土日（日中）担当回数"]
        count_table_obj.ONCALL_HOLIDAY_NIGHTTIME = value[
            "オンコール土日（夜間）担当回数"
        ]
        count_table_obj.ONCALL_COUNT = value["オンコール対応件数"]
        count_table_obj.ENGEL_COUNT = value["エンゼルケア対応件数"]
        count_table_obj.NENKYU = value["年休（全日）"]
        count_table_obj.NENKYU_HALF = value["年休（半日）"]
        count_table_obj.TIKOKU = value["遅刻"]
        count_table_obj.SOUTAI = value["早退"]
        count_table_obj.KEKKIN = value["欠勤"]
        count_table_obj.SYUTTYOU = value["出張（全日）"]
        count_table_obj.SYUTTYOU_HALF = value["出張（半日）"]
        count_table_obj.REFLESH = value["リフレッシュ休暇"]
        count_table_obj.MILEAGE = value["走行距離"]
        count_table_obj.TIMEOFF = value["時間休"]
        count_table_obj.HALFWAY_THROUGH = value["中抜け"]

        try:
            await merge_count_table(count_table_obj, making_id)
        except Exception as e:
            print(e)

    return redirect(f"/month-calc-table/{startday}/{worktype}/{url_y_and_m}")
