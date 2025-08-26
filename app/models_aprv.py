from datetime import datetime

from . import db


class Approval(db.Model):
    __tablename__ = "M_APPROVAL"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    STAFFID = db.Column(
        db.Integer, db.ForeignKey("M_STAFFINFO.STAFFID"), index=True, nullable=False
    )
    TEAM_CODE = db.Column(
        db.Integer, db.ForeignKey("M_TEAM.CODE"), index=True, nullable=False
    )
    TYPE = db.Column(db.String(10), index=True, nullable=False)
    GROUPNAME = db.Column(db.String(50), nullable=False)

    def __init__(self, STAFFID):
        self.STAFFID = STAFFID
        # self.TYPE = TYPE
        # self.GROUPNAME = GROUPNAME


class NotificationList(db.Model):
    __tablename__ = "D_NOTIFICATION_LIST"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    STAFFID = db.Column(
        db.Integer, db.ForeignKey("M_STAFFINFO.STAFFID"), index=True, nullable=False
    )
    NOTICE_DAYTIME = db.Column(db.DateTime(), index=True, default=datetime.now())
    N_CODE = db.Column(
        db.Integer, db.ForeignKey("M_NOTIFICATION.CODE"), index=True, nullable=False
    )
    STATUS = db.Column(db.Integer, index=True, nullable=False, default=0)
    START_DAY = db.Column(db.Date)
    START_TIME = db.Column(db.Time, nullable=True)
    END_DAY = db.Column(db.Date, nullable=True)
    END_TIME = db.Column(db.Time, nullable=True)
    REMARK = db.Column(db.String(255))

    paid_holiday_log = db.relationship("PaidHolidayLog", backref="D_NOTIFICATION_LIST")

    def __init__(
        self,
        STAFFID,
        NOTICE_DAYTIME,
        N_CODE,
        START_DAY,
        START_TIME,
        END_DAY,
        END_TIME,
        REMARK,
    ):
        self.STAFFID = STAFFID
        self.NOTICE_DAYTIME = NOTICE_DAYTIME
        self.N_CODE = N_CODE
        self.START_DAY = START_DAY
        self.START_TIME = START_TIME
        self.END_DAY = END_DAY
        self.END_TIME = END_TIME
        self.REMARK = REMARK


class PaidHolidayLog(db.Model):
    __tablename__ = "D_PAIDHOLIDAY_LOG"
    id = db.Column(
        db.Integer, primary_key=True, autoincrement=True, index=True, nullable=False
    )
    STAFFID = db.Column(
        db.Integer,
        db.ForeignKey("M_RECORD_PAIDHOLIDAY.STAFFID"),
        index=True,
        nullable=False,
    )
    REMAIN_DAYS = db.Column(db.Float, nullable=True)
    NOTIFICATION_id = db.Column(
        db.Integer, db.ForeignKey("D_NOTIFICATION_LIST.id"), index=True, nullable=True
    )
    TIME_REST_FLAG = db.Column(db.Boolean, nullable=True)
    CARRY_FORWARD = db.Column(db.Float, nullable=True)
    REMARK = db.Column(db.String(256), nullable=True)

    def __init__(
        self,
        # id,
        STAFFID,
        REMAIN_TIMES,
        NOTIFICATION_id,
        TIME_REST_FLAG,
        CARRY_FORWARD=None,
        REMARK=None,
    ):
        # self.id = id
        self.STAFFID = STAFFID
        self.REMAIN_TIMES = REMAIN_TIMES
        self.TIME_REST_FLAG = TIME_REST_FLAG
        self.NOTIFICATION_id = NOTIFICATION_id
        self.CARRY_FORWARD = CARRY_FORWARD
        self.REMARK = REMARK

    def to_dict(self):
        return {
            "id": self.id,
            "staff_id": self.STAFFID,
            "remain_times": self.REMAIN_TIMES,
            "time_flag": self.TIME_REST_FLAG,
            "notification_id": self.NOTIFICATION_id,
            "carry": self.CARRY_FORWARD,
            "remark": self.REMARK,
        }
