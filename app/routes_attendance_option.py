"""
**********
勤怠アプリ
2022/04版
**********
"""

import os
from datetime import datetime, timedelta, date
from decimal import Decimal, ROUND_HALF_UP
from dateutil.relativedelta import relativedelta
from monthdelta import monthmod
from functools import wraps

from flask import render_template, flash, redirect, request, session
from flask.helpers import url_for
from flask_login.utils import login_required
from flask_login import current_user, login_user
from flask_login import logout_user
from flask import abort
from werkzeug.security import generate_password_hash

from . import app, db
from .forms import ResetPasswordForm, SaveForm, SelectMonthForm
from .models import User, Attendance, StaffLogin


os.environ.get('SECRET_KEY') or 'you-will-never-guess'
app.permanent_session_lifetime = timedelta(minutes=360)


"""***** 月選択設定 *****"""


@ app.route('/index_select/<STAFFID>/<int:intFlg>', methods=['GET', 'POST'])
@ login_required
def index_select(STAFFID, intFlg):
    Attendances = Attendance.query.filter_by(STAFFID=STAFFID).all()
    STAFFID = STAFFID
    stf_login = StaffLogin.query.filter_by(STAFFID=current_user.STAFFID).first()
    shin = Attendance.query.filter_by(STAFFID=STAFFID)
    u = User.query.get(STAFFID)
    team = u.TEAM_CODE  # この職員のチームコード
    jobtype = u.JOBTYPE_CODE # この職員の職種
            
    ##### index表示関連 #####
    form_month = SelectMonthForm()
    form = SaveForm()
    
    tbl_clm = ["日付", "曜日", "oncall", "oncall対応件数", "engel対応件数",
               "開始時間", "終了時間", "走行距離", "届出（午前）", "残業申請", "備考", "届出（午後）"]
    wk = ["日", "土", "月", "火", "水", "木", "金"]
    ptn = ["^[0-9０-９]+$", "^[0-9.０-９．]+$"]
    specification = ["readonly", "checked", "selected", "hidden"]
    typ = ["submit", "text", "time", "checkbox", "number", "date"]
    
    ##### 月選択 #####
    if form_month.validate_on_submit():
        if request.form.get('workday_name'):
            workday_data_list = request.form.get('workday_name').split('-')
            session["workday_data"] = request.form.get('workday_name') 
            session["y"] = int(workday_data_list[0])
            session["m"] = int(workday_data_list[1])
            
            
            
            
        return redirect(url_for('indextime', STAFFID=STAFFID, intFlg=intFlg))
            
    return render_template('attendance/index.html', title='ホーム', u=u, typ=typ, form_month=form_month, form=form,
                           tbl_clm=tbl_clm, specification=specification, session=session, team=team, jobtype=jobtype,
                           stf_login=stf_login)


"""***** 社員によるパスワードリセットページ *****"""


@app.route('/reset_token_self', methods=['GET', 'POST'])
@login_required
def reset_token_self():
    STAFFID = current_user.STAFFID
    Attendances = Attendance.query.filter_by(STAFFID=STAFFID).all()
    u = User.query.get(STAFFID)
    stf_login = StaffLogin.query.filter_by(STAFFID=current_user.STAFFID).first() 

    hid_a = ""
    hid_b = "hidden"
    form = ResetPasswordForm()
    if form.validate_on_submit():
        STAFFID = STAFFID
        
        if form.PASSWORD.data != form.PASSWORD2.data:
            hid_a = "hidden"
            hid_b = ""
            return render_template('attendance/reset_token_self.html', title='Reset Password', form=form, STAFFID=STAFFID,
                                   Attendances=Attendances, u=u, hid_a=hid_a, hid_b=hid_b)
        elif form.PASSWORD.data == form.PASSWORD2.data: 
            HASHED_PASSWORD = generate_password_hash(form.PASSWORD.data)
            ADMIN = form.ADMIN.data

            StaffLogin.query.filter_by(STAFFID=STAFFID).update(
                dict(PASSWORD_HASH=HASHED_PASSWORD, ADMIN=ADMIN))
            db.session.commit()
            
            flash('パスワードを変更しました。')
            
            return redirect(url_for('select_links'))

    if form.errors:
        flash("エラーが発生しました。")

    return render_template('attendance/reset_token_self.html', title='Reset Password', form=form, STAFFID=STAFFID, Attendances=Attendances,
                           u=u, hid_a=hid_a, hid_b=hid_b, stf_login=stf_login)