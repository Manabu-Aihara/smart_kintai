import pytest
from pytest_mock import MockerFixture
import re
from datetime import date

from app.holiday_to_attendance import read_alert_json


def test_match_regex():
    p = re.compile(r"\d{4}")
    m = p.match("2023")
    print(m)
    assert re.fullmatch(p, "2023")


# @pytest.mark.skip
def test_read_alert_json(mocker: MockerFixture):
    # monkeypatch.setattr("datetime.date.today", lambda: date(2025, 3, 1))
    # mocker.patch("datetime.today", return_value=date(2025, 3, 1))
    test_remain = read_alert_json("8")
    assert test_remain == 0
