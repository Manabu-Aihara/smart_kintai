from datetime import datetime
from enum import IntEnum
from typing import List, Tuple

from flask import render_template, redirect, request
from flask_login import current_user
from flask_login.utils import login_required

from . import app, db
from .common_func import GetPullDownList
from .models import User, Notification, SystemInfo, RecordPaidHoliday
from .models_aprv import NotificationList, Approval, PaidHolidayLog
from .errors import not_admin
from .approval_util import toggle_notification_type, NoZeroTable
from .approval_contact import (
    make_system_skype_object,
    SkypeRelatedException,
    check_skype_account,
)
from .holiday_acquisition import HolidayAcquire

"""
    戻り値に代入される変数名は、必ずstf_login！！
    """
# この関数注意！current_userそのまま返らず
# def appare_global_staff() -> StaffLoggin:
#     current_staff = StaffLoggin.query.get(current_user.STAFFID)
#     return current_staff


# フラグ関数、現urlを取得
# 2度使用するためこちら
def get_current_url_flag() -> bool:
    current_url = request.path
    flag = False
    flag = True if "/approval-list/charge" in current_url else flag
    return flag


# フラグ関数、直前のurlを取得
# 2度使用するためこちら
def get_url_past_flag() -> bool:
    past = request.referrer
    flag = False
    flag = True if "charge" in past else flag
    return flag


# 個別申請リストページ
@app.route("/notification-list/<STAFFID>", methods=["GET"])
@login_required
def get_notification_list(STAFFID):
    # 00：00：00処理ユーティリティメソッド
    table_objects = NoZeroTable(NotificationList)
    table_objects.convert_value_to_none(
        table_objects.select_zero_date_tables,
        "START_TIME",
        "END_TIME",
    )

    user_basic_info: User = (
        db.session.query(User.STAFFID, User.LNAME, User.FNAME)
        .filter(User.STAFFID == STAFFID)
        .first()
    )
    user_notification_list = (
        db.session.query(
            NotificationList.NOTICE_DAYTIME,
            Notification.NAME,
            NotificationList.START_DAY,
            NotificationList.START_TIME,
            NotificationList.END_DAY,
            NotificationList.END_TIME,
            NotificationList.REMARK,
            NotificationList.id,
            NotificationList.STAFFID,
        )
        .filter(NotificationList.STAFFID == STAFFID)
        .join(Notification, Notification.CODE == NotificationList.N_CODE)
        .all()
    )

    # 年休エリア
    holiday_obj = HolidayAcquire(STAFFID)
    start_list, end_list = holiday_obj.print_acquisition_data()
    try:
        holiday_obj.print_remains()
    except TypeError as e:
        enable_holidays = (None, None)
        remain_exce_info = f"※{e}"
    else:
        enable_holidays = holiday_obj.convert_tuple(holiday_obj.print_remains())
        remain_exce_info = ""

    recognized_holidays = holiday_obj.convert_tuple(holiday_obj.sum_notify_times())

    return render_template(
        "attendance/notification_list.html",
        uinfo=user_basic_info,
        nlst=user_notification_list,
        f=get_current_url_flag(),
        h_items=zip(start_list, end_list),
        recognized=recognized_holidays,
        remains=enable_holidays,
        exce=remain_exce_info,
        stf_login=current_user,
    )


class StatusEnum(IntEnum):
    申請中 = 0
    承認済 = 1
    未承認 = 2


# 権限のないユーザーがurl直書きにより、閲覧を防ぐデコレーター
def auth_approval_user(func):
    def wrapper(*args, **kwargs):
        if current_user:
            approval_certificate_user = (
                db.session.query(Approval)
                .filter(Approval.STAFFID == current_user.STAFFID)
                .first()
            )
            if approval_certificate_user is None:
                return not_admin()
            # else:
            #     return func(approval_certificate_user)
        return func(*args, **kwargs)

    return wrapper


# 承認待ちリストページ
@app.route("/approval-list/charge", methods=["GET"])
@login_required
@auth_approval_user
# def get_middle_approval(approval_user):
def get_middle_approval():
    # 00：00：00処理ユーティリティクラス
    table_objects = NoZeroTable(NotificationList)
    table_objects.convert_value_to_none(
        table_objects.select_zero_date_tables,
        "START_TIME",
        "END_TIME",
    )

    all_notification_list = (
        NotificationList.query.with_entities(
            NotificationList.NOTICE_DAYTIME,
            NotificationList.STAFFID,
            User.LNAME,
            User.FNAME,
            Notification.NAME,
            NotificationList.STATUS,
            NotificationList.START_DAY,
            NotificationList.START_TIME,
            NotificationList.END_DAY,
            NotificationList.END_TIME,
            NotificationList.id,
        )
        # .filter(NotificationList.STATUS==0)
        .join(User, User.STAFFID == NotificationList.STAFFID, isouter=True)
        .join(Notification, Notification.CODE == NotificationList.N_CODE)
        .all()
    )

    return render_template(
        "attendance/notification_list.html",
        nlst=all_notification_list,
        f=get_current_url_flag(),
        s_enum=StatusEnum,
        stf_login=current_user,
    )


# 承認詳細ページ
@app.route("/confirm/<STAFFID>/<id>", methods=["GET"])
@login_required
def get_individual_approval(id: int, STAFFID=None):
    notification_row = NotificationList.query.get(id)

    data_list = []
    # 内容
    data_list.append(toggle_notification_type(Notification, notification_row.N_CODE))
    # 対象日
    data_list.append(notification_row.START_DAY)
    # 対象終了日
    data_list.append(notification_row.END_DAY)
    # 開始時刻
    data_list.append(notification_row.START_TIME)
    # 終了時刻
    data_list.append(notification_row.END_TIME)
    # 備考
    data_list.append(notification_row.REMARK)
    # 承認状態
    data_list.append(StatusEnum(notification_row.STATUS).name)
    # そしてNotificationList.id
    data_list.append(notification_row.id)

    # 申請待ちユーザー
    approval_wait_user = User.query.get(STAFFID)

    return render_template(
        "attendance/approval_confirm.html",
        one_data=data_list,
        f=get_url_past_flag(),
        w_usr=approval_wait_user,
        stf_login=current_user,
    )


# 届出内容対照を返す関数
def get_notification_content_list():
    Notification_list = GetPullDownList(
        Notification, Notification.CODE, Notification.NAME, Notification.CODE
    )
    return Notification_list


# 申請入力フォームページ
@app.route("/approval-form", methods=["GET", "POST"])
@login_required
def get_notification_form():
    # if request.method == 'GET':
    notification_all = get_notification_content_list()

    user_detail = User.query.get(current_user.STAFFID)
    user_worktime = (
        db.session.query(RecordPaidHoliday.BASETIMES_PAIDHOLIDAY)
        .filter(RecordPaidHoliday.STAFFID == current_user.STAFFID)
        .first()
    )

    return render_template(
        "attendance/approval_form.html",
        n_all=notification_all,
        worktime=user_worktime.BASETIMES_PAIDHOLIDAY,
        stf_login=user_detail,
    )


# elif request.method == 'POST':

"""
    request.form(input name)から値を取り出しlistに追加
    Param:
        form_data: List[str]
    Return:
        list_data: list
    """


def retrieve_form_data(form_data: List[str]) -> list:
    list_data = []
    for fdata in form_data:
        list_data.append(request.form.get(fdata))

    return list_data


# 申請確認ページ
# @.route('/confirm', methods=['POST'])
# @login_required
# def post_notification():
#     # 取り出したいformの項目
#     approval_list = ['start-day', 'end-day', 'start-time', 'end-time', 'remark']
#     form_list_data = retrieve_form_data(approval_list)

#     # 数値(CODE)を文字列(NAME)に入れ替え
#     form_content: str = toggle_notification_type(Notification, int(request.form.get('content')))
#     # 先頭に挿入
#     form_list_data.insert(0, form_content)

#     return render_template('attendance/approval_confirm.html',
#                         one_data=form_list_data,
#                         f=get_url_past_flag(),
#                         stf_login=current_user)


# DBinsert & skype送信ページ
@app.route("/regist", methods=["POST"])
@login_required
def append_approval():
    approval_list = [
        "content",
        "start-day",
        "end-day",
        "start-time",
        "end-time",
        "remark",
    ]
    form_list_data = retrieve_form_data(approval_list)

    # end-day空白の際
    if form_list_data[2] == "":
        form_list_data[2] = None

    # 注意: start-day, start-time, end_day...の順
    one_notification = NotificationList(
        current_user.STAFFID,
        datetime.now(),
        form_list_data[0],
        form_list_data[1],
        form_list_data[3],
        form_list_data[2],
        form_list_data[4],
        form_list_data[5],
    )

    # skypeにて、申請の通知
    # 所属コード
    team_code = (
        db.session.query(User.TEAM_CODE)
        .filter(User.STAFFID == current_user.STAFFID)
        .first()
    )

    approval_member: Approval = (
        db.session.query(Approval)
        .filter(Approval.TEAM_CODE == team_code.TEAM_CODE)
        .first()
    )

    # 承認者SkypeID
    skype_approval_account = (
        db.session.query(SystemInfo)
        .filter(SystemInfo.STAFFID == approval_member.STAFFID)
        .first()
    )

    # 送信メッセージ
    asking_user = User.query.get(current_user.STAFFID)
    asking_message = f"「{asking_user.LNAME} {asking_user.FNAME}」さんから申請依頼が出ています。\n\
        {request.url_root}approval-list/charge"

    # こっちからでも出来なくはない
    # skype_approval_obj = make_skype_object(skype_approval_account.MAIL, skype_approval_account.MICRO_PASS)

    skype_system_obj = make_system_skype_object()

    ps = "データベーステーブルSystemInfoのSKYPE_IDを確認してください。"
    result_report = "申請が出来ませんでした。"
    try:
        # Skypeシステム（仲介）から承認者へ送信
        check_skype_account(skype_approval_account.SKYPE_ID, approval_member.STAFFID)
    except SkypeRelatedException as skype_exception:
        return render_template(
            "error/exception01.html",
            title="Exception Message",
            message=skype_exception,
            ps=ps,
            repo=result_report,
        )
    else:
        db.session.add(one_notification)
        db.session.commit()

        channel = skype_system_obj.contacts[skype_approval_account.SKYPE_ID].chat
        channel.sendMsg(asking_message)

        return redirect("/")


"""
    申請依頼に対して、許可か拒否か、DBupdate
    Param:
        id: int 申請id
        judgement: int
    Return:
        : None
    """


def update_status(id: int, judgement: int) -> None:
    detail_notification: NotificationList = NotificationList.query.get(id)
    detail_notification.STATUS = judgement

    db.session.merge(detail_notification)
    db.session.commit()


"""
    @Param
        staff_id: int
        id: int 申請id
    @Return
        : None DBinsert処理
    """


def insert_pay_log(staff_id: int, id: int) -> None:
    # 時間休かどうか
    detail_notification: NotificationList = db.session.get(NotificationList, id)
    if detail_notification.N_CODE in [10, 11, 12, 13, 14, 15]:
        time_rest_flag: bool = True
    else:
        time_rest_flag: bool = False

    holiday_obj = HolidayAcquire(staff_id)
    notify_time_else = holiday_obj.get_notification_rests(id)

    if isinstance(notify_time_else, float):
        try:
            remain_time = holiday_obj.print_remains()
        except TypeError as e:
            raise e
        else:
            pay_log_obj = PaidHolidayLog(
                staff_id, remain_time - notify_time_else, id, time_rest_flag
            )
            db.session.add(pay_log_obj)
            db.session.commit()
    else:
        print(notify_time_else)


# 申請に対して、承認
@app.route("/approval_judge/<STAFFID>/<id>/<status>", methods=["POST"])
@login_required
def change_status_judge(id, STAFFID, status: str):
    # 承認待ちユーザー
    approval_wait_user = (
        db.session.query(SystemInfo).filter(SystemInfo.STAFFID == STAFFID).first()
    )
    # 承認するユーザー
    approval_reply_user = SystemInfo.query.filter(
        SystemInfo.STAFFID == current_user.STAFFID
    ).first()
    # 承認判断対象
    target_notification = NotificationList.query.get(id)

    def reply_approval_message(
        status: str, comment: str = request.form.get("comment")
    ) -> str:
        return f"{target_notification.START_DAY}: {toggle_notification_type(Notification, target_notification.N_CODE)}\
                \n{target_notification.REMARK}\n{StatusEnum(int(status)).name}です。\n\n{comment}"

    # 承認者よりコメントをメールで
    # send_mail(approval_reply_user.MAIL, approval_wait_user.MAIL,
    #           approval_reply_user.MAIL_PASS, approval_reply_message)
    skype_system_obj = make_system_skype_object()
    # こっちからでも出来なくはない
    # skype_user_obj = make_skype_object(approval_wait_user.MAIL, approval_wait_user.MICRO_PASS)

    ps = "データベーステーブルM_SYSTEMINFOのSKYPE_IDを確認してください。"
    out_report = "承認が完了しませんでした。"
    try:
        check_skype_account(approval_wait_user.SKYPE_ID, STAFFID)
    except SkypeRelatedException as e:
        print(e)
        return render_template(
            "error/exception01.html",
            title="Exception Message",
            message=e,
            ps=ps,
            repo=out_report,
        )
    else:
        out_report = "承認が出来ませんでした。未承認にします。"
        if int(status) == 1:
            try:
                insert_pay_log(STAFFID, id)
            except TypeError as e:
                update_status(id, 2)
                channel = skype_system_obj.contacts[approval_wait_user.SKYPE_ID].chat
                reply_messege = reply_approval_message("2", "年休が足りません。")
                channel.sendMsg(reply_messege)
                return render_template(
                    "error/exception02.html",
                    title="Exception Message",
                    sid=STAFFID,
                    repo=out_report,
                    exception=e,
                )

        update_status(id, status)
        channel = skype_system_obj.contacts[approval_wait_user.SKYPE_ID].chat
        reply_messege = reply_approval_message(status)
        channel.sendMsg(reply_messege)

    # やはりこちらはダメ、url_forクセがすごい
    # return redirect(url_for('get_middle_approval'))
    return redirect("/approval-list/charge?")
