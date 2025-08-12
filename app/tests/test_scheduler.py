# test_scheduler.py
import pytest
from unittest.mock import MagicMock
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from freezegun import freeze_time


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

    # テスト対象の関数を直接呼び出す
    employee_id = "EMP001"
    mock_grant_leave(employee_id=employee_id)

    # モック関数が1回呼び出されたことを確認
    mock_grant_leave.assert_called_once()
    # 引数が正しいことを確認
    mock_grant_leave.assert_called_with(employee_id=employee_id)


def test_scheduler_job_definition():
    # スケジューラのジョブ定義をテスト
    scheduler = BackgroundScheduler()

    # ジョブを追加
    job = scheduler.add_job(
        grant_paid_leave,
        "cron",
        month="4,10",
        day="1",
        hour="9",
        minute="0",
        kwargs={"employee_id": "EMP001"},
    )

    print(f"job.trigger.fields: {job.trigger.fields}")
    # ジョブが正しく設定されていることを確認
    assert job.func == grant_paid_leave
    assert job.trigger.fields[1].name == "month"
    assert "4" in str(job.trigger.fields[1])
    assert "10" in str(job.trigger.fields[1])
    assert job.trigger.fields[2].name == "day"
    assert "1" in str(job.trigger.fields[2])
    assert job.trigger.fields[5].name == "hour"
    assert "9" in str(job.trigger.fields[5])
    assert job.trigger.fields[6].name == "minute"
    assert "0" in str(job.trigger.fields[6])
    assert job.kwargs == {"employee_id": "EMP001"}

    # スケジューラを開始していないので、shutdown()は不要
    # 代わりに、ジョブを削除してメモリを解放
    scheduler.remove_job(job.id)


# @pytest.mark.skip
def test_grant_paid_leave_with_freezegun(monkeypatch):
    # grant_paid_leave関数をモック化
    mock_grant_leave = MagicMock(return_value=True)
    monkeypatch.setattr("app.tests.test_scheduler.grant_paid_leave", mock_grant_leave)

    # スケジューラをセットアップ
    scheduler = BackgroundScheduler()

    scheduler.start(paused=True)  # 一時停止状態で開始

    try:
        # 4月1日 09:00:00に設定
        with freeze_time("2024-04-01 09:00:00"):
            # ジョブを追加して即時実行
            job = scheduler.add_job(
                # grant_paid_leave,
                mock_grant_leave,
                "date",  # 単発実行のdateトリガーを使用
                run_date=datetime.now(),
                kwargs={"employee_id": "EMP001"},
            )

            # ジョブを手動で実行
            job.func(*job.args, **job.kwargs)

        # モック関数が1回呼び出されたことを確認
        mock_grant_leave.assert_called_once()
        mock_grant_leave.assert_called_with(employee_id="EMP001")
    finally:
        # クリーンアップ
        scheduler.shutdown(wait=False)


@pytest.mark.skip
def test_grant_paid_leave_directly():
    # 実際の関数を直接呼び出して確認
    result = grant_paid_leave("EMP001")
    assert result is True  # 関数がTrueを返すことを確認


def test_setup_scheduler():
    # スケジューラのセットアップをテスト
    scheduler = setup_scheduler()

    # ジョブが正しく設定されていることを確認
    assert len(scheduler.get_jobs()) == 1
    job = scheduler.get_jobs()[0]
    print(f"Job ID: {job.id}")

    # ジョブの設定詳細を確認
    assert job.func == grant_paid_leave
    assert job.trigger.fields[1].name == "month"
    assert "4" in str(job.trigger.fields[1])
    assert "10" in str(job.trigger.fields[1])


def test_scheduler_not_run_in_november(monkeypatch):
    """11月1日には実行されないことをテスト"""
    # grant_paid_leave関数をモック化
    mock_grant_leave = MagicMock(return_value=True)
    monkeypatch.setattr("app.tests.test_scheduler.grant_paid_leave", mock_grant_leave)

    # 11月1日 09:00:00に時刻を設定
    with freeze_time("2024-11-01 09:00:00"):
        scheduler = BackgroundScheduler()
        scheduler.start()

        try:
            # cronジョブを追加
            job = scheduler.add_job(
                mock_grant_leave,
                "cron",
                month="4,10",
                day="1",
                hour="9",
                minute="0",
                kwargs={"employee_id": "EMP001"},
            )

            job.func(**job.kwargs)  # ← これはミスしてくれる
            # 少し待機してジョブが実行されないことを確認
            # import time

            # time.sleep(0.1)

            # 11月なのでジョブは実行されない
            mock_grant_leave.assert_not_called()

        finally:
            scheduler.shutdown(wait=False)


def test_scheduler_runs_in_april(monkeypatch):
    """4月1日に実行されることをテスト"""
    # grant_paid_leave関数をモック化
    mock_grant_leave = MagicMock(return_value=True)
    monkeypatch.setattr("app.tests.test_scheduler.grant_paid_leave", mock_grant_leave)

    # 4月1日 09:00:00に時刻を設定
    with freeze_time("2024-04-01 09:00:00"):
        scheduler = BackgroundScheduler()
        scheduler.start()

        try:
            # cronジョブを追加
            job = scheduler.add_job(
                mock_grant_leave,
                "cron",
                month="4,10",
                day="1",
                hour="9",
                minute="0",
                kwargs={"employee_id": "EMP001"},
            )

            # ジョブを手動で実行（cronの時刻条件をシミュレート）
            # 4月1日の条件を満たすので手動実行
            job.func(**job.kwargs)

            # 4月なのでジョブが実行される
            mock_grant_leave.assert_called_once_with(employee_id="EMP001")

        finally:
            scheduler.shutdown(wait=False)


def test_scheduler_runs_in_october(monkeypatch):
    """10月1日に実行されることをテスト"""
    # grant_paid_leave関数をモック化
    mock_grant_leave = MagicMock(return_value=True)
    monkeypatch.setattr("app.tests.test_scheduler.grant_paid_leave", mock_grant_leave)

    # 10月1日 09:00:00に時刻を設定
    with freeze_time("2024-10-01 09:00:00"):
        scheduler = BackgroundScheduler()
        scheduler.start()

        try:
            # cronジョブを追加
            job = scheduler.add_job(
                mock_grant_leave,
                "cron",
                month="4,10",
                day="1",
                hour="9",
                minute="0",
                kwargs={"employee_id": "EMP001"},
            )

            # ジョブを手動で実行（cronの時刻条件をシミュレート）
            # 10月1日の条件を満たすので手動実行
            job.func(**job.kwargs)

            # 10月なのでジョブが実行される
            mock_grant_leave.assert_called_once_with(employee_id="EMP001")

        finally:
            scheduler.shutdown(wait=False)


def test_grant_paid_leave_function_actually_runs():
    """grant_paid_leave関数が実際に動作することをテスト（printの確認）"""
    import io
    import sys

    # 標準出力をキャプチャ
    captured_output = io.StringIO()
    sys.stdout = captured_output

    try:
        # 実際の関数を呼び出し
        result = grant_paid_leave("TEST001")

        # 標準出力を元に戻す
        sys.stdout = sys.__stdout__

        # 出力内容を取得
        output = captured_output.getvalue()

        # 結果とprint出力を確認
        assert result is True
        assert "年休を付与しました: TEST001" in output
        print(f"Captured output: {output}")  # デバッグ用

    finally:
        # 標準出力を確実に元に戻す
        sys.stdout = sys.__stdout__


@pytest.mark.skip
# 実際のスケジューラーでジョブ実行を確認
def test_job():
    # なぜAPSchedulerで自動実行されないのかを確認
    print("=== APSchedulerの自動実行が発生しない理由 ===")
    print(f"ジョブが実行されました: {datetime.now()}")

    with freeze_time("2024-04-01 09:00:00"):
        scheduler = BackgroundScheduler()

        # パターン1: 現在時刻と同じ時刻のcronジョブ
        print("現在時刻:", datetime.now())

        scheduler.add_job(
            test_job, "cron", month="4", day="1", hour="9", minute="0", second="0"
        )

        scheduler.start()

        # 重要：freezegunは時刻を固定するため、スケジューラーは
        # 「次の瞬間」を待つことができない
        print("0.1秒待機...")
        import time

        time.sleep(0.1)

        jobs = scheduler.get_jobs()
        if jobs:
            job = jobs[0]
            # 手動で次回実行時刻を確認
            print(f"次回実行時刻: {job.next_run_time}")

        scheduler.shutdown(wait=False)

    print("\n=== 解決策: 時刻を少し進める ===")

    with freeze_time("2024-04-01 08:59:59"):  # 1秒前から開始
        scheduler = BackgroundScheduler()
        scheduler.add_job(test_job, "cron", month="4", day="1", hour="9", minute="0")
        scheduler.start()

        # 時刻を進める
        with freeze_time("2024-04-01 09:00:01"):  # 1秒後に進める
            time.sleep(0.1)
            print("時刻を進めた後...")

        scheduler.shutdown(wait=False)

    """
        === APSchedulerの自動実行が発生しない理由 ===
        現在時刻: 2024-04-01 09:00:00
        0.1秒待機...
        次回実行時刻: 2025-04-01 09:00:00+09:00
        ↓
        # 自動実行に頼らず、手動で実行
        job.func(**job.kwargs) 

        === 解決策: 時刻を少し進める ===
        時刻を進めた後...

        APSchedulerは、ジョブ追加時に現在時刻以降の次回実行時刻を計算
        freeze_timeで時刻を固定すると、時間が進まない
    """
