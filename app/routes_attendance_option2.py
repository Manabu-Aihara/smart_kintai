import os
from datetime import timedelta

from flask import render_template, flash, redirect
from flask.helpers import url_for
from flask_login.utils import login_required
from flask_login import current_user
from werkzeug.security import generate_password_hash

from . import app, db
from .forms import ResetPasswordForm
from .models import User, StaffLogin


os.environ.get("SECRET_KEY") or "you-will-never-guess"
app.permanent_session_lifetime = timedelta(minutes=360)


"""***** 社員によるパスワードリセットページ *****"""


@app.route("/reset_token_self", methods=["GET", "POST"])
@login_required
def reset_token_self():
    stf_login = db.session.get(StaffLogin, current_user.STAFFID)

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
            # ADMIN = form.ADMIN.data

            stf_login.PASSWORD_HASH = HASHED_PASSWORD
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
