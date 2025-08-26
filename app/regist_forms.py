from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    SelectField,
    DateField,
    FloatField,
    validators,
)
from wtforms.validators import Optional

from .common_func import GetData
from .models import Department, Team, Contract, JobType, Post


class UserRegistModelForm(FlaskForm):
    busyo_list = GetData(Department, Department.CODE, Department.NAME, Department.CODE)
    syozoku_list = GetData(Team, Team.CODE, Team.NAME, Team.CODE)
    keitai_list = GetData(
        Contract,
        Contract.CONTRACT_CODE,
        Contract.NAME,
        Contract.CONTRACT_CODE,
    )
    syokusyu_list = GetData(
        JobType, JobType.JOBTYPE_CODE, JobType.NAME, JobType.JOBTYPE_CODE
    )
    post_list = GetData(Post, Post.CODE, Post.NAME, Post.CODE)

    department = SelectField(
        "部門",
        choices=[(busyo[0], busyo[1]) for busyo in busyo_list],
        coerce=int,
        validators=[Optional()],
    )
    team = SelectField(
        "所属",
        choices=[(team[0], team[1]) for team in syozoku_list],
        coerce=int,
        validators=[Optional()],
    )
    contract = SelectField(
        "契約形態",
        choices=[(keitai[0], keitai[1]) for keitai in keitai_list],
        coerce=int,
        validators=[Optional()],
    )
    job_type = SelectField(
        "職種",
        choices=[(syokusyu[0], syokusyu[1]) for syokusyu in syokusyu_list],
        coerce=int,
        validators=[Optional()],
    )
    post_code = SelectField(
        "役職",
        choices=[(post[0], post[1]) for post in post_list],
        coerce=int,
        validators=[Optional()],
    )

    lname = StringField("苗字", validators=[Optional()])
    fname = StringField("名前", validators=[Optional()])
    lkana = StringField("苗字（カナ）", validators=[Optional()])
    fkana = StringField("名前（カナ）", validators=[Optional()])
    zip = StringField("郵便番号", validators=[Optional()])
    address1 = StringField("住所１", validators=[Optional()])
    address2 = StringField("住所２", validators=[Optional()])
    tel1 = StringField("固定電話", validators=[Optional()])
    tel2 = StringField("携帯電話", validators=[Optional()])
    birthday = DateField("誕生日", format="%Y-%m-%d", validators=[Optional()])
    inday = DateField("入職日", format="%Y-%m-%d", validators=[Optional()])
    outday = DateField("離職日", format="%Y-%m-%d", validators=[Optional()])
    standday = DateField("独立日", format="%Y-%m-%d", validators=[Optional()])
    social_insurance = SelectField(
        "社会保険",
        choices=[("0", "無"), ("1", "有")],
        coerce=int,
        validators=[Optional()],
    )
    employee_insurance = SelectField(
        "雇用保険",
        choices=[("0", "無"), ("1", "有")],
        coerce=int,
        validators=[Optional()],
    )
    experience = SelectField(
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


class SystemRegistModelForm(FlaskForm):
    mail_address = StringField("Mail Adress", validators=[Optional()])
    mail_password = StringField("Mail Password", validators=[Optional()])
    microsoft_password = StringField("Microsoft Password", validators=[Optional()])
    pay_password = StringField("給与明細Password", validators=[Optional()])
    kanamic_password = StringField("カナミックPassword", validators=[Optional()])
    zoom_password = StringField("Zoom Password", validators=[Optional()])


class HolidayRegistModelForm(FlaskForm):
    holiday_name = StringField("1日の勤務時間", validators=[Optional()])
    holiday_date = DateField(
        "1日の年休時間(価値)", format="%Y-%m-%d", validators=[Optional()]
    )
