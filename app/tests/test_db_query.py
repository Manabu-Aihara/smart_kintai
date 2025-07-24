from datetime import date
from sqlalchemy import or_, and_
from app import db


def test_attendance_count(app_context):
    from app.models import Attendance

    n_absence_list = ["8", "17", "18", "19", "20"]

    filters = [
        Attendance.STAFFID == 152,
        Attendance.WORKDAY >= date(2023, 4, 1),
        Attendance.WORKDAY <= date(2025, 3, 31),
        Attendance.NOTIFICATION.notin_(n_absence_list),
        or_(
            Attendance.NOTIFICATION.in_(["3", "5", "9"]),
            and_(
                ~Attendance.NOTIFICATION.in_(["3", "5", "9"]),
                Attendance.STARTTIME != "00:00",
            ),
        ),
    ]

    count = db.session.query(Attendance.WORKDAY).filter(*filters).count()

    print(f"Count of attendances: {count}")
    # Assert the count is as expected
    assert count == 481
