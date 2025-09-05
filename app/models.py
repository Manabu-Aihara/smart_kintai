from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous.url_safe import URLSafeTimedSerializer as Serializer

from . import app, db, login_manager

# SQLAlchemyのマイグレーションツール Alambic導入時のトラブルシューティングまとめ
# https://www.sria.co.jp/blog/2021/06/5545/
from .models_aprv import Approval, NotificationList
from .models_tt import EventORM


class User(db.Model):
    __tablename__ = "M_STAFFINFO"
    STAFFID = db.Column(db.Integer, primary_key=True, index=True, nullable=False)
    DEPARTMENT_CODE = db.Column(db.Integer, index=True, nullable=True)
    TEAM_CODE = db.Column(db.Integer, index=True, nullable=True)
    CONTRACT_CODE = db.Column(db.Integer, index=True, nullable=True)
    JOBTYPE_CODE = db.Column(db.Integer, index=True, nullable=True)
    POST_CODE = db.Column(db.Integer, index=True, nullable=True)
    LNAME = db.Column(db.String(50), index=True, nullable=True)
    FNAME = db.Column(db.String(50), index=True, nullable=True)
    LKANA = db.Column(db.String(50), index=True, nullable=True)
    FKANA = db.Column(db.String(50), index=True, nullable=True)
    POST = db.Column(db.String(10), index=True, nullable=True)
    ADRESS1 = db.Column(db.String(50), index=True, nullable=True)
    ADRESS2 = db.Column(db.String(50), index=True, nullable=True)
    TEL1 = db.Column(db.String(50), index=True, nullable=True)
    TEL2 = db.Column(db.String(50), index=True, nullable=True)
    BIRTHDAY = db.Column(db.DateTime, index=True, nullable=True)
    INDAY = db.Column(db.DateTime, index=True, nullable=True)
    OUTDAY = db.Column(db.DateTime, index=True, nullable=True)
    STANDDAY = db.Column(db.DateTime, index=True, nullable=True)
    SOCIAL_INSURANCE = db.Column(db.Integer, index=True, nullable=True)
    EMPLOYMENT_INSURANCE = db.Column(db.Integer, index=True, nullable=True)
    EXPERIENCE = db.Column(db.Integer, index=True, nullable=True)
    TABLET = db.Column(db.Integer, index=True, nullable=True)
    SINGLE = db.Column(db.Integer, index=True, nullable=True)
    SUPPORT = db.Column(db.Integer, index=True, nullable=True)
    HOUSE = db.Column(db.Integer, index=True, nullable=True)
    DISTANCE = db.Column(db.Float, index=True, nullable=True)
    REMARK = db.Column(db.String(100), index=True, nullable=True)
    DISPLAY = db.Column(db.Boolean, index=True, nullable=False)
    system = db.relationship("SystemInfo", backref="M_STAFFINFO")
    login = db.relationship("StaffLogin", backref="M_STAFFINFO")
    job_contract = db.relationship("StaffJobContract", backref="M_STAFFINFO")
    holiday_contract = db.relationship("StaffHolidayContract", backref="M_STAFFINFO")
    paid_holiday = db.relationship("RecordPaidHoliday", backref="M_STAFFINFO")
    approval = db.relationship("Approval", backref="M_STAFFINFO")
    notification_list = db.relationship("NotificationList", backref="M_STAFFINFO")

    def __init__(self, STAFFID):
        self.STAFFID = STAFFID


class SystemInfo(db.Model):
    __tablename__ = "M_SYSTEMINFO"
    STAFFID = db.Column(
        db.Integer,
        db.ForeignKey("M_STAFFINFO.STAFFID"),
        primary_key=True,
        index=True,
        nullable=False,
    )
    MAIL = db.Column(db.String(50), index=True, nullable=True)
    MAIL_PASS = db.Column(db.String(50), index=True, nullable=True)
    MICRO_PASS = db.Column(db.String(50), index=True, nullable=True)
    SKYPE_ID = db.Column(db.String(50), index=False, nullable=True)
    PAY_PASS = db.Column(db.String(50), index=True, nullable=True)
    KANAMIC_PASS = db.Column(db.String(50), index=True, nullable=True)
    ZOOM_PASS = db.Column(db.String(50), index=True, nullable=True)

    def __init__(self, STAFFID):
        self.STAFFID = STAFFID


class CollateralTemplate(db.Model):
    __tablename__ = "M_TIMECARD_TEMPLATE"
    JOBTYPE_CODE = db.Column(db.Integer, primary_key=True, index=True, nullable=False)
    CONTRACT_CODE = db.Column(db.Integer, primary_key=True, index=True, nullable=False)
    TEMPLATE_NO = db.Column(db.Integer, index=True, nullable=False)

    """
    sqlalchemy.exc.AmbiguousForeignKeysError:
    Could not determine join condition between parent/child tables on relationship ...
    - there are multiple foreign key paths linking the tables.
    Specify the 'foreign_keys' argument, providing a list of those columns 
    which should be counted as containing a foreign key reference to the parent table.
    """
    # job_history = relationship("D_JOB_HISTORY")
    # https://stackoverflow.com/questions/75756897/reference-a-relationship-with-multiple-foreign-keys-in-sqlalchemy
    # job_history = relationship(
    #     "D_JOB_HISTORY",
    #     # foreign_keys="[D_JOB_HISTORY.JOBTYPE_CODE, D_JOB_HISTORY.CONTRACT_CODE]",
    #     back_populates="timecard_template",
    # )

    def __init__(self, JOBTYPE_CODE, CONTRACT_CODE, TEMPLATE_NO):
        self.JOBTYPE_CODE = JOBTYPE_CODE
        self.CONTRACT_CODE = CONTRACT_CODE
        self.TEMPLATE_NO = TEMPLATE_NO


class StaffJobContract(db.Model):
    __tablename__ = "D_JOB_HISTORY"
    # 複合主キー！重複でも表示させるため、START_DAYを加える
    __table_args__ = (db.PrimaryKeyConstraint("STAFFID", "START_DAY"),)
    # __table_args__ = (
    #     ForeignKeyConstraint(
    #         ["JOBTYPE_CODE", "CONTRACT_CODE"],
    #         ["M_TIMECARD_TEMPLATE.JOBTYPE_CODE", "M_TIMECARD_TEMPLATE.CONTRACT_CODE"],
    #     ),
    # )
    STAFFID = db.Column(
        db.Integer,
        db.ForeignKey("M_STAFFINFO.STAFFID"),
        # primary_key=True,
        index=True,
        nullable=False,
    )
    JOBTYPE_CODE = db.Column(
        db.Integer,
        db.ForeignKey("M_TIMECARD_TEMPLATE.JOBTYPE_CODE"),
        index=True,
        nullable=False,
    )
    CONTRACT_CODE = db.Column(
        db.Integer,
        db.ForeignKey("M_TIMECARD_TEMPLATE.CONTRACT_CODE"),
        index=True,
        nullable=False,
    )
    # JOBTYPE_CODE = db.Column(Integer, index=True, nullable=False)
    # CONTRACT_CODE = db.Column(Integer, index=True, nullable=False)
    """
    2024/8/15 リレーション機能追加
    SQLAlchemy multiple foreign keys in one mapped class to the same primary key
    https://stackoverflow.com/questions/22355890/sqlalchemy-multiple-foreign-keys-in-one-mapped-class-to-the-same-primary-key
    """
    jobtype = db.relationship(
        "CollateralTemplate", foreign_keys=[JOBTYPE_CODE], uselist=True
    )
    constract = db.relationship(
        "CollateralTemplate", foreign_keys=[CONTRACT_CODE], uselist=True
    )

    PART_WORKTIME = db.Column(db.Float, index=True, nullable=True)
    START_DAY = db.Column(db.Date, index=True, nullable=False)
    END_DAY = db.Column(db.Date, index=True, nullable=True)

    # timecard_template = relationship(
    #     "M_TIMECARD_TEMPLATE",
    #     # foreign_keys="[M_TIMECARD_TEMPLATE.JOBTYPE_CODE, M_TIMECARD_TEMPLATE.CONTRACT_CODE]",
    #     back_populates="job_history",
    #     uselist=True,
    # )

    def __init__(
        self, STAFFID, JOBTYPE_CODE, CONTRACT_CODE, PART_WORKTIME, START_DAY, END_DAY
    ):
        self.STAFFID = STAFFID
        self.JOBTYPE_CODE = JOBTYPE_CODE
        self.CONTRACT_CODE = CONTRACT_CODE
        self.PART_WORKTIME = PART_WORKTIME
        self.START_DAY = START_DAY
        self.END_DAY = END_DAY


class StaffHolidayContract(db.Model):
    __tablename__ = "D_HOLIDAY_HISTORY"
    # 複合主キー！重複でも表示させるため、START_DAYを加える
    __table_args__ = (db.PrimaryKeyConstraint("STAFFID", "START_DAY"),)

    STAFFID = db.Column(
        db.Integer,
        db.ForeignKey("M_STAFFINFO.STAFFID"),
        index=True,
        nullable=False,
    )
    HOLIDAY_TIME = db.Column(db.Float, index=True, nullable=False)
    START_DAY = db.Column(db.Date, index=True, nullable=False)
    END_DAY = db.Column(db.Date, index=True, nullable=True)

    def __init__(self, STAFFID, HOLIDAY_TIME, START_DAY, END_DAY):
        self.STAFFID = STAFFID
        self.HOLIDAY_TIME = HOLIDAY_TIME
        self.START_DAY = START_DAY
        self.END_DAY = END_DAY


class Notification(db.Model):
    __tablename__ = "M_NOTIFICATION"
    CODE = db.Column(db.Integer, primary_key=True, index=True, nullable=False)
    NAME = db.Column(db.String(32), index=True, nullable=False)
    notification_list = db.relationship("NotificationList", backref="M_NOTIFICATION")

    def __init__(self, CODE, NAME):
        self.CODE = CODE
        self.NAME = NAME


class Department(db.Model):
    __tablename__ = "M_DEPARTMENT"
    CODE = db.Column(db.Integer, primary_key=True, index=True, nullable=False)
    NAME = db.Column(db.String(50), index=True, nullable=True)

    def __init__(self, CODE):
        self.CODE = CODE


class Team(db.Model):
    __tablename__ = "M_TEAM"
    CODE = db.Column(db.Integer, primary_key=True, index=True, nullable=False)
    NAME = db.Column(db.String(50), index=True, nullable=False)
    SHORTNAME = db.Column(db.String(50), index=True, nullable=False)
    todo = db.relationship("TodoOrm", backref="M_TEAM")
    event = db.relationship("EventORM", backref="M_TEAM")

    def __init__(self, CODE):
        self.CODE = CODE


class JobType(db.Model):
    __tablename__ = "M_JOBTYPE"
    JOBTYPE_CODE = db.Column(db.Integer, primary_key=True, index=True, nullable=False)
    NAME = db.Column(db.String(50), index=True, nullable=False)
    SHORTNAME = db.Column(db.String(50), index=True, nullable=False)

    def __init__(self, JOBTYPE_CODE, NAME, SHORTNAME):
        self.JOBTYPE_CODE = JOBTYPE_CODE
        self.NAME = NAME
        self.SHORTNAME = SHORTNAME


class Contract(db.Model):
    __tablename__ = "M_CONTRACT"
    CONTRACT_CODE = db.Column(db.Integer, primary_key=True, index=True, nullable=False)
    NAME = db.Column(db.String(50), index=True, nullable=True)
    SHORTNAME = db.Column(db.String(50), index=True, nullable=False)
    WORKTIME = db.Column(db.Float, nullable=True)
    table_of_count = db.relationship("TableOfCount", backref="M_CONTRACT")

    def __init__(self, CONTRACT_CODE):
        self.CODE = CONTRACT_CODE


class Post(db.Model):
    __tablename__ = "M_POST"
    CODE = db.Column(db.Integer, primary_key=True, index=True, nullable=False)
    NAME = db.Column(db.String(50), index=True, nullable=True)

    def __init__(self, CODE):
        self.CODE = CODE


class StaffLogin(db.Model, UserMixin):
    __tablename__ = "M_LOGGININFO"
    id = db.Column(db.Integer, primary_key=True)
    STAFFID = db.Column(
        db.Integer,
        db.ForeignKey("M_STAFFINFO.STAFFID"),
        unique=True,
        index=True,
        nullable=False,
    )
    PASSWORD_HASH = db.Column(db.String(128), index=True, nullable=True)
    ADMIN = db.Column(db.Boolean, index=True, nullable=True)
    attendance = db.relationship("Attendance", backref="M_LOGGININFO")
    table_of_count = db.relationship("TableOfCount", backref="M_LOGGININFO")
    event = db.relationship("EventORM", backref="M_LOGGININFO")

    def __init__(self, STAFFID, PASSWORD, ADMIN):
        self.STAFFID = STAFFID
        self.PASSWORD_HASH = generate_password_hash(PASSWORD)
        self.ADMIN = ADMIN

    def check_password(self, PASSWORD):
        return check_password_hash(self.PASSWORD_HASH, PASSWORD)

    def is_admin(self):
        return self.ADMIN

    def get_id(self):
        """明示しなくても動作する。デフォルトではself.idを返すので、注意!"""
        """Flask-Loginで使用するユーザーIDを返す。STAFFIDを使用する"""
        return str(self.STAFFID)

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(app.config["SECRET_KEY"], expires_sec)
        return s.dumps({"user_id": self.STAFFID}).decode("utf-8")

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config["SECRET_KEY"])
        try:
            user_id = s.loads(token)["user_id"]
        except Exception as e:
            # return None
            print(e)
        else:
            return db.session.query(StaffLogin).filter(StaffLogin.STAFFID == user_id)


@login_manager.user_loader
def load_user(STAFFID):
    return (
        db.session.query(StaffLogin).filter(StaffLogin.STAFFID == int(STAFFID)).first()
    )


class Attendance(db.Model):
    __tablename__ = "M_ATTENDANCE"
    id = db.Column(db.Integer, primary_key=True)
    STAFFID = db.Column(db.Integer, db.ForeignKey("M_LOGGININFO.STAFFID"), index=True)
    WORKDAY = db.Column(db.Date, index=True, nullable=True)
    HOLIDAY = db.Column(db.String(32), index=True, nullable=True)
    STARTTIME = db.Column(db.String(32), index=True, nullable=True)  # 出勤時間
    ENDTIME = db.Column(db.String(32), index=True, nullable=True)  # 退勤時間
    MILEAGE = db.Column(db.String(32), index=True, nullable=True)  # 走行距離
    ONCALL = db.Column(db.String(32), index=True, nullable=True)  # オンコール当番
    ONCALL_COUNT = db.Column(db.String(32), index=True, nullable=True)  # オンコール回数
    ENGEL_COUNT = db.Column(db.String(32), index=True, nullable=True)  # エンゼルケア
    NOTIFICATION = db.Column(db.String(32), index=True, nullable=True)  # 届出（午前）
    NOTIFICATION2 = db.Column(db.String(32), index=True, nullable=True)  # 届出（午後）
    OVERTIME = db.Column(db.String(32), index=True, nullable=True)  # 残業時間申請
    ALCOHOL = db.Column(db.Integer, index=True, nullable=True)
    REMARK = db.Column(db.String(100), index=True, nullable=True)  # 備考

    def __init__(
        self,
        STAFFID,
        WORKDAY,
        HOLIDAY,
        STARTTIME,
        ENDTIME,
        MILEAGE,
        ONCALL,
        ONCALL_COUNT,
        ENGEL_COUNT,
        NOTIFICATION,
        NOTIFICATION2,
        OVERTIME,
        ALCOHOL,
        REMARK,
    ):
        self.STAFFID = STAFFID
        self.WORKDAY = WORKDAY
        self.HOLIDAY = HOLIDAY
        self.STARTTIME = STARTTIME
        self.ENDTIME = ENDTIME
        self.MILEAGE = MILEAGE
        self.ONCALL = ONCALL
        self.ONCALL_COUNT = ONCALL_COUNT
        self.ENGEL_COUNT = ENGEL_COUNT
        self.NOTIFICATION = NOTIFICATION
        self.NOTIFICATION2 = NOTIFICATION2
        self.OVERTIME = OVERTIME
        self.ALCOHOL = ALCOHOL
        self.REMARK = REMARK


class RecordPaidHoliday(db.Model):  # 年休関連
    __tablename__ = "M_RECORD_PAIDHOLIDAY"
    STAFFID = db.Column(
        db.Integer,
        db.ForeignKey("M_STAFFINFO.STAFFID"),
        primary_key=True,
        index=True,
        nullable=False,
    )
    LAST_DATEGRANT = db.Column(
        db.DateTime, index=True, nullable=True
    )  # 今回付与年月日 ← HolidayDayCountにより、算出できる
    NEXT_DATEGRANT = db.Column(
        db.DateTime, index=True, nullable=True
    )  # 次回付与年月日 ← HolidayDayCountにより、算出できる
    USED_PAIDHOLIDAY = db.Column(
        db.Float, index=True, nullable=True
    )  # 使用日数 ← 頻繁に変更が発生するため、PaidHolidayLogに移行が良い
    REMAIN_PAIDHOLIDAY = db.Column(
        db.Float, index=True, nullable=True
    )  # 残日数 ← 頻繁に変更が発生するため、PaidHolidayLogに移行が良い
    # TEAM_CODE = db.Column(Integer, index=True, nullable=True)
    # CONTRACT_CODE = db.Column(Integer, index=True, nullable=True)
    LAST_CARRIEDOVER = db.Column(
        db.Float, index=True, nullable=True
    )  # 前回繰越日数 ← 1年に一回変更あるため、PaidHolidayLogに移行が良いか
    ATENDANCE_YEAR = db.Column(
        db.Integer, index=True, nullable=True
    )  # 年間出勤日数（年休べース） ← 1年に一回変更あるため、PaidHolidayLogに移行が良いか
    WORK_TIME = db.Column(
        db.Float, index=True, nullable=True
    )  # 職員勤務時間 ← 契約変更の場合あり
    BASETIMES_PAIDHOLIDAY = db.Column(
        db.Float, index=True, nullable=True
    )  # 規定の年休時間 ← 契約変更の場合あり
    ACQUISITION_TYPE = db.Column(
        db.String(1)
    )  # 年休付与タイプ ← ATENDANCE_YEARにより、変更される
    holiday_log = db.relationship("PaidHolidayLog", backref="M_RECORD_PAIDHOLIDAY")

    def __init__(self, STAFFID):
        self.STAFFID = STAFFID


class TableOfCount(db.Model):
    __tablename__ = "M_TABLE_OF_COUNTER"
    id = db.Column(db.String(15), primary_key=True)
    STAFFID = db.Column(
        db.Integer,
        db.ForeignKey("M_LOGGININFO.STAFFID"),
        index=True,
        nullable=False,
    )
    CONTRACT_CODE = db.Column(
        db.Integer, db.ForeignKey("M_CONTRACT.CONTRACT_CODE"), index=True, nullable=True
    )
    YEAR_MONTH = db.Column(db.String(10), index=True, nullable=False)
    ONCALL = db.Column(db.Integer, index=True, nullable=True)
    ONCALL_HOLIDAY_ONE_DAY = db.Column(db.Integer, index=True, nullable=True)
    ONCALL_HOLIDAY_DAYTIME = db.Column(db.Integer, index=True, nullable=True)
    ONCALL_HOLIDAY_NIGHTTIME = db.Column(db.Integer, index=True, nullable=True)
    ONCALL_COUNT = db.Column(db.Integer, index=True, nullable=True)
    ENGEL_COUNT = db.Column(db.Integer, index=True, nullable=True)
    NENKYU = db.Column(db.Integer, index=True, nullable=True)
    NENKYU_HALF = db.Column(db.Integer, index=True, nullable=True)
    TIKOKU = db.Column(db.Integer, index=True, nullable=True)
    SOUTAI = db.Column(db.Integer, index=True, nullable=True)
    KEKKIN = db.Column(db.Integer, index=True, nullable=True)
    SYUTTYOU = db.Column(db.Integer, index=True, nullable=True)
    SYUTTYOU_HALF = db.Column(db.Integer, index=True, nullable=True)
    REFLESH = db.Column(db.Integer, index=True, nullable=True)
    MILEAGE = db.Column(db.Float, index=True, nullable=True)
    SUM_WORKTIME = db.Column(db.Float, index=True, nullable=True)
    SUM_REAL_WORKTIME = db.Column(db.Float, index=True, nullable=True)
    OVERTIME = db.Column(db.Float, index=True, nullable=True)
    HOLIDAY_WORK = db.Column(db.Float, index=True, nullable=True)
    WORKDAY_COUNT = db.Column(db.Integer, index=True, nullable=True)
    SUM_WORKTIME_10 = db.Column(db.Float, index=True, nullable=True)
    OVERTIME_10 = db.Column(db.Float, index=True, nullable=True)
    HOLIDAY_WORK_10 = db.Column(db.Float, index=True, nullable=True)
    TIMEOFF = db.Column(db.Integer, index=True, nullable=True)
    HALFWAY_THROUGH = db.Column(db.Integer, index=True, nullable=True)

    def __init__(self, staff_id: int):
        super().__init__()
        self.STAFFID = staff_id
