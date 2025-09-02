import os
from datetime import datetime, timedelta, date

from flask import render_template, flash, redirect, request, session
from flask.helpers import url_for
from flask_login.utils import login_required
from flask_login import current_user, login_user
from werkzeug.security import generate_password_hash

from . import app, db
from .forms import ResetPasswordForm, SaveForm, SelectMonthForm
from .models import User, Attendance, StaffLogin


os.environ.get("SECRET_KEY") or "you-will-never-guess"
app.permanent_session_lifetime = timedelta(minutes=360)


"""***** 月選択設定 *****"""


@app.route("/index_select/<STAFFID>/<int:intFlg>", methods=["GET", "POST"])
@login_required
def index_select(STAFFID, intFlg):
    stf_login = db.session.get(StaffLogin, STAFFID)
    user = db.session.get(User, STAFFID)
    team = user.TEAM_CODE  # この職員のチームコード
    jobtype = user.JOBTYPE_CODE  # この職員の職種

    ##### index表示関連 #####
    form_month = SelectMonthForm()
    form = SaveForm()

    tbl_clm = [
        "日付",
        "曜日",
        "oncall",
        "oncall対応件数",
        "engel対応件数",
        "開始時間",
        "終了時間",
        "走行距離",
        "届出（午前）",
        "残業申請",
        "備考",
        "届出（午後）",
    ]
    wk = ["日", "土", "月", "火", "水", "木", "金"]
    ptn = ["^[0-9０-９]+$", "^[0-9.０-９．]+$"]

    ##### 月選択 #####
    if form_month.validate_on_submit():
        if request.form.get("workday_name"):
            workday_data_list = request.form.get("workday_name").split("-")
            session["workday_data"] = request.form.get("workday_name")
            session["y"] = int(workday_data_list[0])
            session["m"] = int(workday_data_list[1])

        return redirect(url_for("indextime", STAFFID=STAFFID, intFlg=intFlg))

    return render_template(
        "attendance/index.html",
        title="ホーム",
        u=user,
        form_month=form_month,
        form=form,
        tbl_clm=tbl_clm,
        session=session,
        team=team,
        jobtype=jobtype,
        stf_login=stf_login,
    )


"""***** 社員によるパスワードリセットページ *****"""


@app.route("/reset_token_self", methods=["GET", "POST"])
@login_required
def reset_token_self():
    stf_login = (
        db.session.query(StaffLogin).filter_by(STAFFID=current_user.STAFFID).first()
    )

    user = db.session.get(User, current_user.STAFFID)
    correct_pass = ""
    uncorrect_pass = "hidden"

    form = ResetPasswordForm()
    if form.validate_on_submit():
        if form.PASSWORD.data != form.PASSWORD2.data:
            correct_pass = "hidden"
            uncorrect_pass = ""
            return render_template(
                "attendance/reset_token_self.html",
                title="Reset Password",
                form=form,
                STAFFID=current_user.STAFFID,
                usr=user,
                correct_pass=correct_pass,
                uncorrect_pass=uncorrect_pass,
            )
        else:
            HASHED_PASSWORD = generate_password_hash(form.PASSWORD.data)
            ADMIN = form.ADMIN.data

            stf_login.update(dict(PASSWORD_HASH=HASHED_PASSWORD, ADMIN=ADMIN))
            db.session.commit()
            flash("パスワードを変更しました。")

            return redirect(url_for("select_links"))

    if form.errors:
        flash("エラーが発生しました。")

    return render_template(
        "attendance/reset_token_self.html",
        title="Reset Password",
        form=form,
        STAFFID=current_user.STAFFID,
        usr=user,
        correct_pass=correct_pass,
        uncorrect_pass=uncorrect_pass,
        stf_login=stf_login,
    )
