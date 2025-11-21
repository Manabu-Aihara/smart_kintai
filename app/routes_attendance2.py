import os
from typing import List, Tuple, Dict, Any, Optional, Union
from datetime import date, timedelta
import calendar
import re
from decimal import Decimal, ROUND_HALF_UP
from itertools import groupby

from flask import render_template, redirect, request, flash
from flask_login.utils import login_required
from flask.helpers import url_for
from sqlalchemy import and_

from . import app, db
from .forms import SelectMonthForm, SaveForm
from .models import User, StaffLogin, Notification, Attendance
from .attendance_query_class import AttendanceQuery
from .calc_work_classes3 import CalcTimeFactory
from .attendance_validate_class import AttendanceValidate
from .new_calendar import NewCalendar
from .common_func import NoneCheck, TimeCheck, blankCheck
from .attendance_util import get_month_workday
from .attendance_logging import AttendanceLogger

# わかりにくいが、日付選択に使うため必要らしい
# from . import routes_attendance_option2

"""
    各契約日の初日-1（後に個数分配列にするため便利）の配列 + その月の最終日
    @Params:
        : Any（クエリーのため） M_TIMECARD_TEMPLATE用
        : int その月の最終日
    @Return
        : list<int>
    !注意: 引数のクエリーが複数ない場合、前契約日-1が入らない
    """


def make_boundary_list(queries: Any, last_day_of_month: int) -> List[int]:
    boundary_list = []
    # 連番の区切りとなるSTART_DAYのリスト
    for query in queries:
        if query.START_DAY is None:
            raise ValueError("START_DAYカラムのあるクエリーを入れてください")
        # 便宜上ここで-1することにより、make_num_repeatで個数を作りやすくする
        boundary_list.append(query.START_DAY.day - 1)

    return boundary_list + [last_day_of_month]


"""
    所定の値を連番にする
    @Params:
        : int | str 連番にしたいもの
        : list make_boundary_list
        : int その添字、1からだろう
    @Return:
        : list<int | str>
    """


def make_num_repeat(
    number: Union[int, str], boundary_list: list, subscript: int
) -> List[Union[int, str]]:
    result_repeat = []
    # TEMPLATE_NOの連番を作る、2回目以降は前の連番の数を引く
    result_repeat.append(
        [number] * (boundary_list[subscript] - (boundary_list[subscript - 1]))
        if subscript > 1
        else [number] * boundary_list[subscript]
    )

    return result_repeat


@app.route("/attendance/<STAFFID>/<reference_flag>/<selected_date>", methods=["GET"])
@login_required
def output_attendance(STAFFID, reference_flag, selected_date):
    # login_user = (
    #     db.session.query(StaffLogin).filter(StaffLogin.STAFFID == STAFFID).first()
    # )
    if app.permanent_session_lifetime == 0:
        return redirect(url_for("logout_mes"))

    form_of_month = SelectMonthForm()
    save_form = SaveForm()

    dow_list = ["月", "火", "水", "木", "金", "土", "日"]
    attendance_all_columns = [
        "当番",
        "oncall対応件数",
        "angel対応件数",
        "開始時間",
        "終了時間",
        "走行距離",
        "届出（午前）",
        "届出（午後）",
        "残業申請",
        "アルコール",
        "実働時間",
        "備考",
    ]
    # attendance_all_columnsのうち、表示するもの
    attendance_columns_list = []
    # 以下、各テンプレートごとの表示制御用、リストの添字はテンプレートの連番に対応
    display_oncall_list = []
    display_oncall_correspond_list = []
    display_engel_list = []
    display_distance_list = []
    display_over_list = []

    staff_id = int(STAFFID)
    target_attend_user = db.session.get(User, staff_id)

    # 参照モードの場合、
    style_mode = ""
    if reference_flag == "3":
        # 参照モード
        style_mode = "pointer-events: none;"

    non_display = "display: none"

    # 日付関連
    selected_year, selected_month = get_month_workday(selected_date)
    new_calendar_obj = NewCalendar(selected_year, selected_month)

    from_date = date(selected_year, selected_month, 1)
    last_day_of_month = calendar.monthrange(selected_year, selected_month)[1]
    to_date = date(selected_year, selected_month, last_day_of_month)
    print(f"Date: {from_date}〜{to_date}")

    holiday_index = new_calendar_obj.get_jp_holidays_num()
    print(f"Anniversary: {holiday_index}")

    # 申請: M_NOTIFICATIONとindexの紐づけ
    notification_items = db.session.query(Notification).all()
    exclude_list = [3, 5, 7, 8, 17, 18, 19, 20]
    notification_pm_list = [
        n for i, n in enumerate(notification_items, 1) if i not in exclude_list
    ]

    # 入力必要項目
    specify_member_list = [
        int(s) for s in os.getenv("TEMPLATE_SPECIFY_MEMBERS").split(",")
    ]

    # クエリーオブジェクト
    attendance_qry_obj = AttendanceQuery(STAFFID, from_date, to_date)

    templates = attendance_qry_obj.get_templates()
    # repeat_list = []
    # for template in templates:
    #     repeat_list.append(template.START_DAY.day)
    # repeat_list = repeat_list + [last_day_of_month]
    print(f"Template query: {templates.all()}")
    repeat_list = make_boundary_list(templates, last_day_of_month)
    print(f"Start days: {repeat_list}")

    # 2次元配列、出力データ用
    # 変数名[日付][項目]
    attendance_key_list = [
        "ID",
        "date",
        "date_DD",
        "dow",
        "oncall",
        "oncall_count",
        "engel_count",
        "start_time",
        "end_time",
        "mileage",
        "notification",
        "notification_pm",
        "over_time",
        "alcohol",
        "worktime",
        "remark",
    ]
    # 各グループごとに新しいattendance_dataを作成
    # グループの日数分だけのデータを作成
    # 2025/6/6 初期化をgroupby内に移動、じゃないと月日数分上書きされる
    # attendance_data: List[Dict[str, Any]] = [{}]
    # # 初期値はNone
    # list_null_16 = [None for i in range(0, 16)]
    # for i in range(to_date.day):
    #     dict_data = dict(zip(attendance_key_list, list_null_16))
    #     attendance_data.append(dict_data)

    attendance_queries = attendance_qry_obj.get_attendance_query()
    # attendance_queries = attendace_qry_obj.get_perfect_contract_attendance()

    # 必要な初期値、意外と多い…
    workday_count: int = 0
    actual_time_sum: float = 0.0
    actual_time_rnd = Decimal("0")
    distance_sum: float = 0.0
    nurse_holiday_work_times: float = 0.0
    holiday_work10_rnd = Decimal("0")
    # 諸々計算クラスファクトリー
    calc_time_factory = CalcTimeFactory()

    # 最終データ初期値
    attendance_table_dict: Dict[str, dict] = {}

    # repeat_listの0は、from_date直前の契約日なので1から
    start_day_subscript = 1
    # TEMPLATE_NOの連番の、2次元配列
    template_repeat = []
    # template_repeatの添字
    template_repeat_subscript = 0

    """ 月の途中の契約変更1回までは対応 """
    # クエリーか、空か、分割のどれかか？
    group_by_data: Union[
        Any, List[int], List[int, Any], List[Any, int]
    ]  # Anyはクエリー
    empty_list = []
    for i, template in enumerate(templates, 1):
        # 出退勤空の場合
        if len(attendance_queries.all()) == 0:
            print("Template pass 1")
            empty_list.append(make_num_repeat(template.TEMPLATE_NO, repeat_list, i))
            # 配列のdementionを1個除く
            group_by_data = sum(empty_list, [])
        # 契約変更日の前が空で、それ以外データ有りの場合
        elif (
            len(
                attendance_queries.filter(Attendance.WORKDAY < template.START_DAY).all()
            )
            == 0
        ):
            print("Template pass 2")
            empty_list.append(make_num_repeat(template.TEMPLATE_NO, repeat_list, i))
            # 変更初日以後のクエリー
            query = attendance_queries.filter(
                Attendance.WORKDAY >= template.START_DAY
            ).all()
            group_by_data = sum(empty_list, []) + query
        # 契約変更日の後が空で、それ以外データ有りの場合
        elif (
            len(
                attendance_queries.filter(
                    Attendance.WORKDAY >= template.START_DAY
                ).all()
            )
            == 0
        ):
            print("Template pass 3")
            empty_list.append(make_num_repeat(template.TEMPLATE_NO, repeat_list, i))
            # 変更初日より前のクエリー
            query = attendance_queries.filter(
                Attendance.WORKDAY < template.START_DAY
            ).all()
            group_by_data = query + sum(empty_list, [])
        # 通常の出退勤データ有りの場合
        else:
            print("Template pass 4")
            # 0.Attendance, 1.D_JOB_HISTORY.JOBTYPE_CODE, 2.D_JOB_HISTORY.CONTRACT_CODE
            # 3.D_JOB_HISTORY.PART_WORKTIME, 4.KinmuTaisei.WORKTIME
            # 5.D_HOLIDAY_HISTORY.HOLIDAY_TIME, 6.M_TIMECARD_TEMPLATE.TEMPLATE_NO,
            group_by_data = attendance_queries

    for idx, group_itr in groupby(
        group_by_data, lambda x: x[6] if not isinstance(x, int) else x[0]
    ):
        print(f"Template number: {idx}")
        # 前者: テンプレートナンバーリスト及び、項目名
        # 後者: keyが日付、valueが各Attendanceの値（dict{項目名, 値}）
        attendance_data: Union[
            Dict[str, Union[list, str]], Dict[int, Dict[str, Any]]
        ] = {}  # 辞書型で初期化

        for template in templates:
            type_in_over = "checkbox" if template.CONTRACT_CODE != 2 else "hidden"
            if staff_id in specify_member_list:
                attendance_columns_list.append(attendance_all_columns)
                display_oncall_list.append("")
                display_oncall_correspond_list.append("")
                display_engel_list.append("")
                display_distance_list.append("")
                display_over_list.append(type_in_over)
            elif template.TEMPLATE_NO == 1:
                attendance_columns_list.append(
                    attendance_all_columns[:5] + attendance_all_columns[6:]
                )
                display_oncall_list.append("")
                display_oncall_correspond_list.append("")
                display_engel_list.append("")
                display_distance_list.append(non_display)
                display_over_list.append(type_in_over)
            elif template.TEMPLATE_NO == 2:
                attendance_columns_list.append(attendance_all_columns[3:])
                display_oncall_list.append(non_display)
                display_oncall_correspond_list.append(non_display)
                display_engel_list.append(non_display)
                display_distance_list.append("")
                display_over_list.append(type_in_over)

        attendance_data["columns"] = attendance_columns_list[template_repeat_subscript]
        attendance_data["oncall_disp"] = display_oncall_list[template_repeat_subscript]
        attendance_data["oncall_crsp_disp"] = display_oncall_correspond_list[
            template_repeat_subscript
        ]
        attendance_data["engel_disp"] = display_engel_list[template_repeat_subscript]
        attendance_data["distance_disp"] = display_distance_list[
            template_repeat_subscript
        ]
        attendance_data["over_time_disp"] = display_over_list[template_repeat_subscript]

        """ ここから複雑 """

        # TEMPLATE_NOの連番を作る
        template_repeat = template_repeat + make_num_repeat(
            idx, repeat_list, start_day_subscript
        )
        # template_repeat.append(
        #     [idx]
        #     * (
        #         repeat_list[start_day_subscript]
        #         - (repeat_list[start_day_subscript - 1] - 1)
        #     )
        #     if start_day_subscript > 1
        #     else [idx] * repeat_list[start_day_subscript]
        # )
        # make by Cursor
        # if start_day_subscript > 1:
        #     # 2回目以降は、前の日付との差分（前の日付は含まない）
        #     days = repeat_list[start_day_subscript] - (
        #         repeat_list[start_day_subscript - 1] - 1
        #     )
        # else:
        #     # 1回目は、次の日付までの差分（1日は含む）
        #     days = repeat_list[start_day_subscript] - repeat_list[0]
        # template_repeat.append([idx] * days)

        # グループの日数分だけループ
        for i in range(0, len(template_repeat[template_repeat_subscript])):
            # TEMPLATE_NOの2番目以降は、1周目カウントの次
            day = (
                i + (repeat_list[start_day_subscript - 1] + 1)
                if start_day_subscript > 1
                else i + 1  # でなければ、1から始まる日付
            )

            # 一旦初期値は""
            list_null_16 = ["" for i in range(0, 16)]
            dict_data = dict(zip(attendance_key_list, list_null_16))
            attendance_data[day] = dict_data

            # 日付(YYYY-MM-DD)
            attendance_data[day]["date"] = date(
                selected_year, selected_month, day
            ).strftime("%Y-%m-%d")
            # 日付(DD)
            attendance_data[day]["date_DD"] = int(
                date(selected_year, selected_month, day).strftime("%d")
            )
            # print(f"Debug: day: {i}")
            # 曜日(日本語)
            attendance_data[day]["dow"] = dow_list[
                (
                    new_calendar_obj.get_monthdays_pair()[
                        i + (repeat_list[start_day_subscript - 1])
                    ][1]
                    if start_day_subscript > 1
                    else new_calendar_obj.get_monthdays_pair()[i][1]
                )
            ]
            # 以下、各表示初期値
            # 開始時間
            # attendance_data[day]["start_time"] = "00:00"
            # # 終了時間
            # attendance_data[day]["end_time"] = "00:00"
            # # 走行距離
            # attendance_data[day]["mileage"] = 0.0

        start_day_subscript += 1
        template_repeat_subscript += 1

        group_list = list(group_itr)
        print(f"List detail: {group_list}")
        for group in group_list:
            attendance_obj = group[0]
            print(attendance_obj)
            if isinstance(attendance_obj, Attendance):
                print("Pass 6")
                print(f"GET何日: {attendance_obj.WORKDAY.day}")

                attendance_data[attendance_obj.WORKDAY.day]["ID"] = attendance_obj.id
                # オンコール当番
                attendance_data[attendance_obj.WORKDAY.day][
                    "oncall"
                ] = attendance_obj.ONCALL
                # オンコール対応
                attendance_data[attendance_obj.WORKDAY.day]["oncall_count"] = NoneCheck(
                    attendance_obj.ONCALL_COUNT
                )
                # エンゼル対応
                attendance_data[attendance_obj.WORKDAY.day]["engel_count"] = NoneCheck(
                    attendance_obj.ENGEL_COUNT
                )
                # 開始時間
                attendance_data[attendance_obj.WORKDAY.day]["start_time"] = TimeCheck(
                    attendance_obj.STARTTIME
                )
                # 終了時間
                attendance_data[attendance_obj.WORKDAY.day]["end_time"] = TimeCheck(
                    attendance_obj.ENDTIME
                )
                # 走行距離
                attendance_data[attendance_obj.WORKDAY.day][
                    "mileage"
                ] = attendance_obj.MILEAGE
                # 申請(AM)
                attendance_data[attendance_obj.WORKDAY.day][
                    "notification"
                ] = attendance_obj.NOTIFICATION
                # 申請(PM)
                attendance_data[attendance_obj.WORKDAY.day][
                    "notification_pm"
                ] = attendance_obj.NOTIFICATION2
                # 残業申請
                attendance_data[attendance_obj.WORKDAY.day][
                    "over_time"
                ] = attendance_obj.OVERTIME
                # アルコールチェック
                attendance_data[attendance_obj.WORKDAY.day][
                    "alcohol"
                ] = attendance_obj.ALCOHOL
                # 備考
                attendance_data[attendance_obj.WORKDAY.day][
                    "remark"
                ] = attendance_obj.REMARK

                calculation_instance = calc_time_factory.get_instance(staff_id=staff_id)
                # 常勤かパートか
                setting_each_time = (
                    (group[3], group[5]) if group[2] == 2 else (group[4], group[4])
                )
                calculation_instance.set_data(
                    setting_each_time[0],
                    setting_each_time[1],
                    attendance_obj.STARTTIME,
                    attendance_obj.ENDTIME,
                    (attendance_obj.NOTIFICATION, attendance_obj.NOTIFICATION2),
                    attendance_obj.OVERTIME,
                    attendance_obj.HOLIDAY,
                )

                # 実働時間
                actual_work_time = calculation_instance.get_actual_work_time()
                print(f"実働時間: {actual_work_time}")
                actual_work_time_str = (
                    re.sub(
                        r"([0-9]{1,2}):([0-9]{2}):00", r"\1:\2", f"{actual_work_time}"
                    )
                    if actual_work_time > timedelta(hours=0)
                    else "0.0"
                )
                attendance_data[attendance_obj.WORKDAY.day][
                    "worktime"
                ] = actual_work_time_str

                actual_second = actual_work_time.total_seconds()

                # real_time = calculation_instance.get_real_time()
                # print(f"リアル時間: {real_time}")
                # 勤務日数
                workday_count += 1 if actual_second != 0.0 else 0

                actual_time_sum += actual_second
                time_sum_normal = actual_time_sum / 3600
                # 実働時間計：10進数
                actual_time_rnd = (
                    Decimal(time_sum_normal).quantize(Decimal("0.01"), ROUND_HALF_UP)
                    if time_sum_normal >= 0
                    else "--:--"
                )

                # 走行距離計
                distance_sum += (
                    float(attendance_obj.MILEAGE)
                    if not isinstance(attendance_obj.MILEAGE, type(None))
                    and attendance_obj.MILEAGE != ""
                    and attendance_obj.MILEAGE != "0.0"
                    else 0
                )

                nurse_holiday_works = calculation_instance.calc_nurse_holiday_work()
                if nurse_holiday_works != 9.99:
                    nurse_holiday_work_times += nurse_holiday_works
                # h_h = nurse_holiday_work_times // (60 * 60)
                # h_m = (nurse_holiday_work_times - h_h * 60 * 60) // 60
                # 看護師休日労働時間計
                # holiday_work60 = h_h + h_m / 100

                holiday_work_10 = nurse_holiday_work_times / (60 * 60)
                # 看護師休日労働時間計：10進数
                holiday_work10_rnd = Decimal(holiday_work_10).quantize(
                    Decimal("0.01"), ROUND_HALF_UP
                )

        attendance_table_dict[f"{idx}"] = attendance_data
        print(f"Debug: template_repeat for {idx}: {template_repeat}")
        # print(f"Debug: template_repeat: {template_repeat}")
        # print(f"Debug: repeat_list: {repeat_list}")
        print(f"Debug: start_day_subscript: {start_day_subscript}")

    # for key, value in attendance_table_dict.items():
    #     print(f"Key: {key} Value: {value}")
    #     for k, v in value.items():
    #         print(f"Inner key: {k} Inner value: {v}")
    # これ何？
    reload_y = request.form.get("reload_h")

    return render_template(
        "attendance/attendance_input.html",
        ref_flag=reference_flag,
        month_form=form_of_month,
        save_form=save_form,
        selected_date=selected_date,
        attd_tbl=attendance_table_dict,
        user=target_attend_user,
        h_idx=holiday_index,
        mode=style_mode,
        select_y=selected_year,
        select_m=selected_month,
        notifi_lst=notification_items,
        notifi_pm_lst=notification_pm_list,
        actual_time_sum=actual_time_rnd,
        work_cnt=workday_count,
        distance_sum=distance_sum,
        holiday_works=holiday_work10_rnd,
        reload_y=reload_y,
    )


def get_move_distance(form_distance: str) -> Optional[str]:
    if form_distance is not None and form_distance != "":
        ZEN = "".join(chr(0xFF01 + j) for j in range(94))
        HAN = "".join(chr(0x21 + k) for k in range(94))
        ZEN2HAN = str.maketrans(ZEN, HAN)
        str_distance = form_distance.translate(ZEN2HAN)

        def is_num(s) -> float:
            try:
                float(s)
            except ValueError:
                return flash("数字以外は入力できません。")
            else:
                return s

        num_distance = is_num(str_distance)

        result_distance = str(
            Decimal(num_distance).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
        )
        return result_distance
    else:
        result_distance = None
        return result_distance


@app.route("/attendance/<STAFFID>/input.do", methods=["POST"])
@login_required
def input_attendance(STAFFID):
    form_of_month = SelectMonthForm()
    selected_form_date = ""
    if form_of_month.validate_on_submit():
        selected_form_date = request.form.get("select_month")  # 選択された日付
        print(f"Select form date: {selected_form_date}")
        return redirect(f"/attendance/{STAFFID}/1/{selected_form_date}")

    print(f"Re-render date: {request.form.get('select_month')}")
    selected_form_date = request.form.get("select_month")  # 選択された日付
    selected_year, selected_month = get_month_workday(selected_form_date)
    new_calendar_obj = NewCalendar(selected_year, selected_month)

    from_date = date(selected_year, selected_month, 1)
    last_day_of_month = calendar.monthrange(selected_year, selected_month)[1]
    to_date = date(selected_year, selected_month, last_day_of_month)
    update_exist_list: List[tuple] = []

    attendace_qry_obj = AttendanceQuery(STAFFID, from_date, to_date)
    # TEMPLATE_NOの連番の、2次元配列
    template_repeat = []
    # repeat_listの0は、from_date直前の契約日なので1から
    start_day_subscript = 1
    # TEMPLATE_NOの連番の、2次元配列
    templates = attendace_qry_obj.get_templates()
    # 連番の区切りとなるSTART_DAYのリスト
    repeat_list = make_boundary_list(templates, last_day_of_month)
    # repeat_list = []
    # for template in templates:
    #     repeat_list.append(template.START_DAY.day)
    # repeat_list = repeat_list + [last_day_of_month]

    for template in templates:
        # TEMPLATE_NOの連番を作る
        template_repeat = template_repeat + make_num_repeat(
            template.TEMPLATE_NO, repeat_list, start_day_subscript
        )
        # template_repeat.append(
        #     [template.TEMPLATE_NO]
        #     * (
        #         repeat_list[start_day_subscript]
        #         - (repeat_list[start_day_subscript - 1] - 1)
        #     )
        #     if start_day_subscript > 1
        #     else [template.TEMPLATE_NO] * repeat_list[start_day_subscript]
        # )
        # make by Cursor
        # if start_day_subscript > 1:
        #     # 2回目以降は、前の日付との差分（前の日付は含まない）
        #     days = (
        #         repeat_list[start_day_subscript] - repeat_list[start_day_subscript - 1]
        #     )
        # else:
        #     # 1回目は、次の日付までの差分（1日は含む）
        #     days = repeat_list[start_day_subscript] - repeat_list[0] + 1
        # template_repeat.append([template.TEMPLATE_NO] * days)
        start_day_subscript += 1

    print(f"Templates in post: {template_repeat}")
    combination_data: List[Tuple[tuple, int]] = list(
        zip(new_calendar_obj.get_monthdays_pair(), sum(template_repeat, []))
    )

    for i, (calendar_pair, temp_no) in enumerate(combination_data):
        form_key = "id" + str(temp_no) + str(i)
        attendance_id = request.form.get(form_key)
        print(f"Debug: Form data - key: {form_key}")
        print(f"Debug: Form data - value: {attendance_id}")
        print(f"Debug: Form data - type: {type(attendance_id)}")
        print(f"Debug: Form data - exists: {form_key in request.form}")

        current_date = request.form.get("date" + str(temp_no) + str(i))
        start_time = TimeCheck(
            request.form.get("begin_time" + str(temp_no) + str(i))
        )  # 開始時間
        finish_time = TimeCheck(
            request.form.get("fin_time" + str(temp_no) + str(i))
        )  # 終了時間
        mileage = request.form.get("distance" + str(temp_no) + str(i))  # 移動距離
        oncall = request.form.get("oncall" + str(temp_no) + str(i))  # オンコール
        oncall_cnt = request.form.get(
            "oncall_cnt" + str(temp_no) + str(i)
        )  # オンコール回数
        engel_cnt = request.form.get("engel" + str(temp_no) + str(i))  # エンゼル回数
        notification = request.form.get(
            "notification" + str(temp_no) + str(i)
        )  # 届出AM
        notification_pm = request.form.get(
            "notification_pm" + str(temp_no) + str(i)
        )  # 届出PM
        overtime = request.form.get("over" + str(temp_no) + str(i))  # 残業
        alcohol = request.form.get("alcohol" + str(temp_no) + str(i))  # アルコール
        remark = request.form.get("remark" + str(temp_no) + str(i))  # 備考

        # 出退勤バリデーションチェック
        attendance_validate_obj = AttendanceValidate(
            start_time,
            finish_time,
            oncall,
            notification,
            notification_pm,
            current_date=current_date,
        )
        comment, key = attendance_validate_obj.validate_attendance()

        work_date = date(selected_year, selected_month, calendar_pair[0])

        flag_insert = 0

        holiday = ""
        if calendar_pair[0] in new_calendar_obj.get_jp_holidays_num():
            # 要は祝日
            holiday = "2"
        elif calendar_pair[1] == 5 or calendar_pair[1] == 6:
            # 要は土日
            holiday = "1"

        ##### 走行距離小数第1位表示に変換 #####
        result_mileage = get_move_distance(mileage)

        Notification_AM = notification
        zangyou = 1 if overtime == "on" else 0
        Notification_PM = notification_pm

        oncall_check: int = 0
        oncall_cnt_value: str = "0"
        engel: str = "0"
        alc: int = 0
        # 登録するかの判定
        if (
            start_time != "00:00"
            or finish_time != "00:00"
            or (
                result_mileage is not None
                and result_mileage != "0.0"
                and result_mileage != ""
            )
            or blankCheck(oncall) is not None
            or blankCheck(oncall_cnt) is not None
            or blankCheck(Notification_AM) is not None
            or blankCheck(Notification_PM) is not None
            or blankCheck(engel_cnt) is not None
            or remark != ""
            or blankCheck(alcohol) is not None
        ):
            print(f"{calendar_pair[0]}日")
            print(f"On call: {oncall}")
            print(f"Engel: {engel_cnt}")
            print(f"Alcohol: {alc}")
            oncall_check = oncall
            if oncall_cnt != "0":
                oncall_cnt_value = oncall_cnt
            if engel_cnt != "0":
                engel = engel_cnt
            if alcohol == "on":
                alc = 1

            # インデントがムズい
            flag_insert = 1 if attendance_id == "" else 0
            if key == "uncorrect" or key == "warning":
                flag_insert = 0
                flash(f"{current_date}{comment}", key)

            # 出退勤保存ログ用
            target_user = db.session.get(User, int(STAFFID))
            updated_user = f"{target_user.LNAME} {target_user.FNAME}"
            updated_month = work_date.month

        # 更新データ準備
        if attendance_id:
            if type(attendance_id) is None:
                raise TypeError("Interrupt update stop!")
            print(f"Debug: Creating setting_item for ID: {attendance_id}")
            setting_item = (
                attendance_id,
                STAFFID,
                work_date,
                holiday,
                start_time,
                finish_time,
                result_mileage,
                oncall_check,
                oncall_cnt_value,
                engel,
                Notification_AM,
                Notification_PM,
                zangyou,
                alc,
                remark,
            )
            update_exist_list.append(setting_item)
            print(
                f"Debug: Added to update_exist_list, current length: {len(update_exist_list)}"
            )

        print(f"Insert: {flag_insert} {work_date} {attendance_id} {start_time}")
        # DB挿入処理
        attendance_add_data = Attendance(
            STAFFID,
            work_date,
            holiday,
            start_time,
            finish_time,
            result_mileage,
            oncall_check,
            oncall_cnt_value,
            engel,
            Notification_AM,
            Notification_PM,
            zangyou,
            alc,
            remark,
        )
        if flag_insert == 1:
            db.session.add(attendance_add_data)
            flash(f"{current_date}{comment}", key)
    db.session.commit()

    called_attendance_list = (
        db.session.query(Attendance)
        .filter(
            and_(
                Attendance.STAFFID == STAFFID,
                Attendance.WORKDAY.between(from_date, to_date),
            )
        )
        .all()
    )
    print(f"Debug: called_attendance_list length: {len(called_attendance_list)}")
    print(f"Debug: update_exist_list length: {len(update_exist_list)}")

    # データの内容確認
    # for i, (called, update) in enumerate(
    #     zip(called_attendance_list, update_exist_list)
    # ):
    #     print(f"Debug: Item {i}")
    #     print(f"Debug: Called - ID: {called.id}, Date: {called.WORKDAY}")
    #     print(f"Debug: Update - ID: {update[0]}, Date: {update[2]}")

    # DB更新処理
    for twin_attendance in tuple(zip(called_attendance_list, update_exist_list)):
        for i, clm_name in enumerate(twin_attendance[0].__table__.c.keys()):
            print(f"Column Data: {clm_name} {twin_attendance[1][i]}")
            # id、日付の順番が関連付けられてなかったら必要
            if clm_name != "id":
                setattr(twin_attendance[0], clm_name, twin_attendance[1][i])
        db.session.merge(twin_attendance[0])
    db.session.commit()

    if updated_user != "" and updated_month != 0:
        # flash(
        #     f"{updated_month}月分の出退勤を{updated_user}さんで保存しました。",
        #     "attendance_log",
        # )
        logger = AttendanceLogger.get_logger(updated_month)
        logger.info(updated_user)

    return redirect(f"/attendance/{STAFFID}/1/{selected_form_date}")
