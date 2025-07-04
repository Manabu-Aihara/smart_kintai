from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    BooleanField,
    SubmitField,
    SelectField,
    IntegerField,
    FloatField,
    validators,
)
from wtforms.fields import DateField
from wtforms.validators import DataRequired, EqualTo, Optional

from . import app, db
from .common_func import GetPullDownList, GetData
from .models import (
    Post,
    Department,
    JobType,
    Team,
    Contract,
)
# from . import routes_attendance_option


class LoginForm(FlaskForm):
    STAFFID = StringField("社員番号", validators=[DataRequired()])
    PASSWORD = PasswordField("パスワード", validators=[DataRequired()])
    remember_me = BooleanField("記憶させる")
    submit = SubmitField("サインイン")


class AdminUserCreateForm(FlaskForm):
    staffid = StringField("社員番号", validators=[DataRequired()])
    password = PasswordField("パスワード", validators=[DataRequired()])
    admin = BooleanField("管理権限の付与")


class AdminUserUpdateForm(FlaskForm):
    STAFFID = StringField("社員番号")
    PASSWORD = PasswordField("パスワード")
    ADMIN = BooleanField("管理権限の付与")


class ResetPasswordForm(FlaskForm):
    PASSWORD = PasswordField("パスワード", validators=[DataRequired()])
    PASSWORD2 = PasswordField("パスワード確認", validators=[DataRequired()])
    ADMIN = BooleanField("管理権限の付与")
    submit = SubmitField("　保　存　")


class DisplayForm(FlaskForm):
    sub = SubmitField("表　示")
    """ 24/9/12 追加 """
    display = BooleanField("非表示")


class TimeForm(FlaskForm):
    sub = SubmitField("提　出")


class DelForm(FlaskForm):
    dlt = SubmitField("削　除")


class UpdateForm(FlaskForm):
    upd = SubmitField("更　新")


class SaveForm(FlaskForm):
    sav = SubmitField("　　　保　　　　存　　　")


class EditForm(FlaskForm):
    sav = SubmitField("　　　編　　　　集　　　")


class SelectMonthForm(FlaskForm):
    slct = SubmitField("選　択")


class SelectYearForm2(FlaskForm):
    slct2 = SubmitField("月選択")


class AddDataUserForm(FlaskForm):

    with app.app_context():
        db.create_all()
        bumon = GetData(Department, Department.CODE, Department.NAME, Department.CODE)
        syozoku = GetData(Team, Team.CODE, Team.NAME, Team.CODE)
        keitai = GetData(
            Contract,
            Contract.CONTRACT_CODE,
            Contract.NAME,
            Contract.CONTRACT_CODE,
        )
        syokusyu = GetData(
            JobType, JobType.JOBTYPE_CODE, JobType.NAME, JobType.JOBTYPE_CODE
        )
        post = GetData(Post, Post.CODE, Post.NAME, Post.CODE)

    department = SelectField(
        "部門",
        choices=[(bumons[0], bumons[1]) for bumons in bumon],
        coerce=int,
        validators=[Optional()],
    )
    team = SelectField(
        "所属",
        choices=[(Teams[0], Teams[1]) for Teams in syozoku],
        coerce=int,
        validators=[Optional()],
    )
    contract = SelectField(
        "契約形態",
        choices=[(keitais[0], keitais[1]) for keitais in keitai],
        coerce=int,
        validators=[Optional()],
    )
    JobType = SelectField(
        "職種",
        choices=[(syokusyus[0], syokusyus[1]) for syokusyus in syokusyu],
        coerce=int,
        validators=[Optional()],
    )
    post_code = SelectField(
        "役職",
        choices=[(posts[0], posts[1]) for posts in post],
        coerce=int,
        validators=[Optional()],
    )

    lname = StringField("苗字", validators=[Optional()])
    fname = StringField("名前", validators=[Optional()])
    lkana = StringField("苗字（カナ）", validators=[Optional()])
    fkana = StringField("名前（カナ）", validators=[Optional()])
    post = StringField("郵便番号", validators=[Optional()])
    adress1 = StringField("住所１", validators=[Optional()])
    adress2 = StringField("住所２", validators=[Optional()])
    tel1 = StringField("固定電話", validators=[Optional()])
    tel2 = StringField("携帯電話", validators=[Optional()])
    birthday = DateField("誕生日", format="%Y-%m-%d", validators=[Optional()])
    inday = DateField("入職日", format="%Y-%m-%d", default=datetime.today())
    outday = DateField("離職日", format="%Y-%m-%d", validators=[Optional()])
    standday = DateField("独立日", format="%Y-%m-%d", validators=[Optional()])
    social = SelectField(
        "社会保険",
        choices=[("0", "無"), ("1", "有")],
        coerce=int,
        validators=[Optional()],
    )
    employee = SelectField(
        "雇用保険",
        choices=[("0", "無"), ("1", "有")],
        coerce=int,
        validators=[Optional()],
    )
    experi = SelectField(
        "経験手当",
        choices=[("0", "無"), ("1", "有")],
        coerce=int,
        validators=[Optional()],
    )
    tablet = SelectField(
        "私物タブレット使用",
        choices=[("0", "無"), ("1", "有")],
        coerce=int,
        validators=[Optional()],
    )
    single = SelectField(
        "ひとり親手当",
        choices=[("0", "無"), ("1", "支給有")],
        coerce=int,
        validators=[Optional()],
    )
    support = SelectField(
        "扶養人数(20歳未満)",
        choices=[("0", ""), ("1", "1"), ("2", "2"), ("3", "3"), ("4", "4")],
        coerce=int,
        validators=[Optional()],
    )
    house = SelectField(
        "住宅手当",
        choices=[("0", "無"), ("1", "支給有")],
        coerce=int,
        validators=[Optional()],
    )
    distance = FloatField(
        "通勤距離(片道)",
        validators=[
            validators.NumberRange(0, 100, "0.0～100.0の数値を入力して下さい。"),
            Optional(),  # 24/7/29 追加
        ],
    )
    remark = StringField("備考", validators=[Optional()])
    m_a = StringField("Mail Adress", validators=[Optional()])
    ml_p = StringField("Mail Password", validators=[Optional()])
    ms_p = StringField("Microsoft Password", validators=[Optional()])
    p_p = StringField("給与明細Password", validators=[Optional()])
    k_p = StringField("カナミックPassword", validators=[Optional()])
    z_p = StringField("Zoom Password", validators=[Optional()])
    worker_time = FloatField("1日の勤務時間", default=0, validators=[Optional()])
    basetime_paidholiday = FloatField(
        "1日の年休時間(価値)", default=0, validators=[Optional()]
    )
    last_carriedover = FloatField("繰越年休日数", default=0, validators=[Optional()])
