"""
**********
勤怠システム
2022/04版
**********
"""

import os
from datetime import datetime

from flask import render_template, flash, redirect, request
from werkzeug.urls import url_parse
from flask.helpers import url_for
from flask_login.utils import login_required
from flask_login import current_user, login_user
from flask_login import logout_user

from . import app
from .database_base import session
from .forms import LoginForm
from .models import User, Attendance, StaffLogin

# from . import routes_attendance
# from . import kinmu_index
from . import routes_approvals, routes_admin
from . import (
    routes_attendance2,
    routes_calc_month_data,
    routes_leave_to_clerk,
    routes_holiday_related,
)


"""***** ログイン後最初のページ *****"""


@app.route("/")
@app.route("/select_links", methods=["GET"])
@login_required
def select_links():
    print(f"Login user: {current_user.STAFFID}")  # デバッグ用
    # STAFFID = current_user.STAFFID
    stf_login = (
        session.query(StaffLogin)
        .filter(StaffLogin.STAFFID == current_user.STAFFID)
        .first()
    )

    Attendances = (
        session.query(Attendance).filter_by(STAFFID=current_user.STAFFID).all()
    )
    user = session.get(User, current_user.STAFFID)

    team = user.TEAM_CODE  # この職員のチームコード
    jobtype = user.JOBTYPE_CODE  # この職員の職種

    this_month = datetime.today().strftime("%Y-%m")

    return render_template(
        "select_links.html",
        title="Select link",
        STAFFID=current_user.STAFFID,
        Attendances=Attendances,
        u=user,
        team=team,
        jobtype=jobtype,
        this_month=this_month,
        stf_login=stf_login,
    )


"""***** ログイン・ログアウト処理 *****"""


@app.route("/logout_mes", methods=["GET"])
def logout_mes():
    return render_template("logout_mes.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("select_links"))

    form = LoginForm()
    if form.validate_on_submit():
        user = (
            session.query(StaffLogin)
            .filter(StaffLogin.STAFFID == form.STAFFID.data)
            .first()
        )
        print(f"Login directly: {user.STAFFID}")
        if user is None or not user.check_password(form.PASSWORD.data):
            flash("ユーザ名かパスワードが違います")
            return redirect(url_for("login"))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get("next")
        if not next_page or url_parse(next_page).netloc != "":
            next_page = url_for("select_links")
        return redirect(next_page)
    return render_template("login.html", title="yoboiryo株式会社 System", form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("logout_mes"))


"""***** WebブラウザのCSSキャッシュ対策 *****"""


@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)


def dated_url_for(endpoint, **values):
    if endpoint == "static":
        filename = values.get("filename", None)
        if filename:
            file_path = os.path.join(app.root_path, endpoint, filename)
            values["q"] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)
