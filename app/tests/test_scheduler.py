# test_scheduler.py
import pytest
from unittest.mock import MagicMock
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import freezegun


# テスト対象の関数
def grant_paid_leave(employee_id):
    print(f"年休を付与しました: {employee_id}")
    return True


# スケジューリングのロジック
def setup_scheduler():
    scheduler = BackgroundScheduler()
    # 4月1日と10月1日に年休を付与するジョブを登録
    scheduler.add_job(
        grant_paid_leave,
        "cron",
        month="4,10",
        day="1",
        hour="9",
        minute="0",
        kwargs={"employee_id": "EMP001"},
    )
    return scheduler


# APSchedulerの動作をテストする
def test_grant_paid_leave_on_april_first():
    # grant_paid_leave関数をモック化
    mock_grant_leave = MagicMock(return_value=True)

    # スケジューラをセットアップ
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        mock_grant_leave,
        "cron",
        month="4",
        day="1",
        hour="9",
        minute="0",
        kwargs={"employee_id": "EMP001"},
    )
    scheduler.start()

    # 3月31日から4月1日に時間を進める
    with freezegun.freeze_time("2024-03-31 08:59:59"):
        pass  # テスト開始時点
    with freezegun.freeze_time("2024-04-01 09:00:01"):
        # ジョブが実行されるまで少し待機
        scheduler.shutdown(wait=False)

    # モック関数が1回呼び出されたことを確認
    mock_grant_leave.assert_called_once()
    # 引数が正しいことを確認
    mock_grant_leave.assert_called_with(employee_id="EMP001")
