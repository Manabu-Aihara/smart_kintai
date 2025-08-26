from dataclasses import dataclass
from datetime import date

from sqlalchemy import and_

from . import db
from .models import (
    User,
    Attendance,
    StaffHolidayContract,
    StaffJobContract,
    JobType,
    Contract,
    CollateralTemplate,
)


@dataclass
class AttendanceQuery:
    staff_id: int
    filter_from_day: date
    filter_to_day: date

    # sub_query: T = None
    # def __init__(self, staff_id: str, sub_query: T) -> None:
    #     self.staff_id = staff_id

    # Max attendance_filters[0:8] index7まで取り出す

    def _get_filter(self) -> list:
        attendance_filters = []
        attendance_filters.append(Attendance.STAFFID == self.staff_id)
        attendance_filters.append(
            Attendance.WORKDAY.between(self.filter_from_day, self.filter_to_day)
        )
        attendance_filters.append(Attendance.STAFFID == User.STAFFID)
        return attendance_filters

    @staticmethod
    def _get_job_filter(part_timer_flag: bool = False):
        attendance_filters = []
        attendance_filters.append(Attendance.STAFFID == StaffJobContract.STAFFID)
        attendance_filters.append(StaffJobContract.START_DAY <= Attendance.WORKDAY)
        attendance_filters.append(StaffJobContract.END_DAY >= Attendance.WORKDAY)
        (
            attendance_filters.append(StaffJobContract.CONTRACT_CODE != 2)
            if part_timer_flag is False
            else attendance_filters.append(StaffJobContract.CONTRACT_CODE == 2)
        )
        return attendance_filters

    @staticmethod
    def _get_holiday_filter():
        attendance_filters = []
        attendance_filters.append(Attendance.STAFFID == StaffHolidayContract.STAFFID)
        attendance_filters.append(StaffHolidayContract.START_DAY <= Attendance.WORKDAY)
        attendance_filters.append(StaffHolidayContract.END_DAY >= Attendance.WORKDAY)
        return attendance_filters

    def _get_template_filter(self):
        attendance_filters = []
        attendance_filters.append(StaffJobContract.STAFFID == self.staff_id)
        attendance_filters.append(
            and_(
                StaffJobContract.START_DAY <= self.filter_to_day,
                StaffJobContract.END_DAY >= self.filter_from_day,
            )
        )
        attendance_filters.append(
            StaffJobContract.JOBTYPE_CODE == CollateralTemplate.JOBTYPE_CODE
        )
        attendance_filters.append(
            StaffJobContract.CONTRACT_CODE == CollateralTemplate.CONTRACT_CODE
        )
        return attendance_filters

    def db_error_handler(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ValueError as e:
                return e

        return wrapper

    @db_error_handler
    def get_templates(self):
        template_filters = self._get_template_filter()
        return (
            db.session.query(
                CollateralTemplate.TEMPLATE_NO,
                # クエリーを増やし、distinctでの重複除去を防ぐ
                # StaffJobContract.JOBTYPE_CODE,
                StaffJobContract.CONTRACT_CODE,
                StaffJobContract.START_DAY,
            )
            .join(
                StaffJobContract,
                and_(
                    StaffJobContract.JOBTYPE_CODE == CollateralTemplate.JOBTYPE_CODE,
                    StaffJobContract.CONTRACT_CODE == CollateralTemplate.CONTRACT_CODE,
                ),
            )
            .filter(and_(*template_filters))
            # GROUP BYを削除し、代わりにDISTINCTを使用
            .distinct()
            .order_by(StaffJobContract.START_DAY)
        )

    @db_error_handler
    def _get_sub_parttime(self):
        attendance_filters = self._get_filter()[0:2] + self._get_holiday_filter()
        attendance_filters.append(Attendance.STAFFID == StaffHolidayContract.STAFFID)

        return (
            db.session.query(
                StaffHolidayContract.STAFFID,
                Attendance.WORKDAY,
                StaffHolidayContract.HOLIDAY_TIME,
            )
            .filter(and_(*attendance_filters))
            .subquery()
        )

    @db_error_handler
    def get_attendance_query(self):
        attendance_filters = (
            self._get_filter()
            + self._get_job_filter()[0:3]
            + self._get_template_filter()[-2:]
        )

        sub_query = self._get_sub_parttime()
        return (
            db.session.query(
                Attendance,
                StaffJobContract.JOBTYPE_CODE,
                StaffJobContract.CONTRACT_CODE,
                StaffJobContract.PART_WORKTIME,
                Contract.WORKTIME,
                sub_query.c.HOLIDAY_TIME,
                CollateralTemplate.TEMPLATE_NO,
            )
            .join(
                StaffJobContract,
                and_(
                    StaffJobContract.STAFFID == Attendance.STAFFID,
                    Attendance.WORKDAY >= StaffJobContract.START_DAY,
                    Attendance.WORKDAY <= StaffJobContract.END_DAY,
                ),
            )
            .join(Contract, Contract.CONTRACT_CODE == StaffJobContract.CONTRACT_CODE)
            .outerjoin(
                sub_query,
                and_(
                    sub_query.c.STAFFID == Attendance.STAFFID,
                    sub_query.c.WORKDAY == Attendance.WORKDAY,
                ),
            )
            .filter(and_(*attendance_filters))
            .order_by(Attendance.STAFFID, Attendance.WORKDAY)
        )

    # 対象年月日の職種や契約時間をスタッフごとに纏める(サブクエリ)
    def _get_sub_clerk_query(self):
        return (
            db.session.query(
                StaffHolidayContract.STAFFID, StaffHolidayContract.HOLIDAY_TIME
            )
            .filter(
                StaffHolidayContract.START_DAY <= self.filter_to_day,
                StaffHolidayContract.END_DAY >= self.filter_to_day,
            )
            .subquery()
        )

    @db_error_handler
    def get_clerical_attendance(self, part_timer_flag: bool):
        clerk_filters = self._get_filter()[1:] + self._get_job_filter(part_timer_flag)

        sub_clerk_query = self._get_sub_clerk_query()
        return (
            db.session.query(
                Attendance,
                User.FNAME,
                User.LNAME,
                StaffJobContract.JOBTYPE_CODE,
                StaffJobContract.CONTRACT_CODE,
                StaffJobContract.PART_WORKTIME,
                # Contract.WORKTIME,
                sub_clerk_query.c.HOLIDAY_TIME,
            )
            # .join(Contract, Contract.CONTRACT_CODE == StaffJobContract.CONTRACT_CODE)
            .outerjoin(sub_clerk_query, sub_clerk_query.c.STAFFID == User.STAFFID)
            .filter(and_(*clerk_filters))
            .order_by(Attendance.STAFFID, Attendance.WORKDAY)
        )

    def get_perfect_contract_attendance(self):
        base_filters = self._get_filter()

        # with get_session() as session:
        queries_for_calc_member = (
            db.session.query(
                Attendance, StaffJobContract, StaffHolidayContract, Contract.WORKTIME
            )
            .join(
                StaffJobContract,
                and_(
                    StaffJobContract.STAFFID == Attendance.STAFFID,
                    Attendance.WORKDAY >= StaffJobContract.START_DAY,  # この条件が重要
                    Attendance.WORKDAY <= StaffJobContract.END_DAY,
                ),
            )
            .join(Contract, Contract.CONTRACT_CODE == StaffJobContract.CONTRACT_CODE)
            .outerjoin(
                StaffHolidayContract,
                and_(
                    StaffHolidayContract.STAFFID == Attendance.STAFFID,
                    Attendance.WORKDAY
                    >= StaffHolidayContract.START_DAY,  # この条件も重要
                    Attendance.WORKDAY <= StaffHolidayContract.END_DAY,
                ),
            )
            .filter(
                and_(
                    *base_filters,
                    # Attendance.WORKDAY >= self.filter_from_day,
                )
            )
            .order_by(StaffJobContract.STAFFID)
        )

        return queries_for_calc_member

    # Query[(User, int)]
    def get_distinct_user_query(self):
        user_filters = self._get_filter()[1:] + self._get_job_filter()[0:3]
        # サブクエリでSTAFFIDごとの最新のSTART_DAYを取得
        # subquery = (
        #     db.session.query(
        #         StaffJobContract.STAFFID,
        #         func.max(StaffJobContract.START_DAY).label("max_start_day"),
        #     )
        #     .group_by(StaffJobContract.STAFFID)
        #     .subquery()
        # )

        # サブクエリとStaffJobContractを結合して、各STAFFIDの最新レコードを取得
        user_order_query = (
            db.session.query(User, StaffJobContract.CONTRACT_CODE)
            # .join(
            #     subquery,
            #     (StaffJobContract.STAFFID == subquery.c.STAFFID)
            #     & (StaffJobContract.START_DAY == subquery.c.max_start_day),
            # )
            .join(User, User.STAFFID == StaffJobContract.STAFFID)
            .filter(and_(*user_filters))
            .order_by(StaffJobContract.START_DAY.desc())
        )
        return user_order_query

    # デバッグ用のクエリ
    def debug_query(self):
        debug_query = (
            db.session.query(
                StaffJobContract.CONTRACT_CODE,
                StaffJobContract.JOBTYPE_CODE,
                JobType.NAME,
                Contract.WORKTIME,
            )
            .join(JobType, JobType.JOBTYPE_CODE == StaffJobContract.JOBTYPE_CODE)
            .join(Contract, Contract.CONTRACT_CODE == StaffJobContract.CONTRACT_CODE)
            .filter(StaffJobContract.STAFFID == self.staff_id)
            .first()
        )
        print(debug_query)  # 結果を確認
