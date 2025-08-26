from typing import List, Dict
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

import pandas as pd
from pandas import Series

from app import db
from .models import RecordPaidHoliday
from .calc_work_classes3 import CalcTimeClass, output_rest_time

"""
    集計結果をSeriesで
    @Params:
        : CalcTimeClass 各種計算クラスオブジェクト
        : list 契約期間ごとのクエリー各種、中タプル
        : int
    @Return:
        : Series
    """


def calc_attendance_of_term(
    setting_time: CalcTimeClass, group_data_list: list, staff_id: int
) -> Series:
    pds = pd.Series

    # 欠勤扱いコード
    n_absence_list: List[str] = ["8", "17", "18", "19", "20"]

    actual_time_sum: float = 0.0
    # 【項目11】実働時間計：60進数
    actual_time60: float = 0.0
    # 【項目12】実働時間計：10進数
    actual_time_rnd: Decimal = 0.0

    real_work_times = []
    # 【項目13】リアル労働時間計：60進数
    real_time: float = 0.0

    over_times = []
    # 【項目17】残業時間計：60進数
    over60: float = 0.0
    # 【項目18】残業時間計：10進数
    over10_rnd: Decimal = 0.0

    nurse_holiday_works = []
    # 【項目22】看護師休日労働時間計：60進数
    holiday_work60: float = 0.0
    # 【項目23】看護師休日労働時間計：10進数
    holiday_work10_rnd: Decimal = 0.0

    # 【項目7】オンコール平日
    on_call_cnt: int = 0
    # 【項目8】オンコール休日
    on_call_holiday_cnt: int = 0
    # 【項目9】オンコール対応
    on_call_correspond_cnt: int = 0
    # 【項目10】エンゼル対応
    engel_correspond_cnt: int = 0

    # 【項目14】
    workday_count: int = 0
    # 【項目15】年休全日
    holiday_cnt: int = 0
    # 【項目16】年休半日
    half_holiday_cnt: int = 0
    # 【項目19】遅刻
    late_cnt: int = 0
    # 【項目20】早退
    leave_early_cnt: int = 0
    # 【項目21】欠勤
    absence_cnt: int = 0
    # 【項目24】出張全日
    trip_cnt: int = 0
    # 【項目25】出張半日
    half_trip_cnt: int = 0
    # 【項目26】リフレッシュ
    reflesh_cnt: int = 0
    # 【項目27】走行距離
    distance_sum: float = 0.0

    # 【項目28】時間休
    timeoff: int = 0
    # 【項目29】中抜け
    halfway_through: int = 0

    # パートタイム契約（CONTRACT_CODE == 2）の場合の代替時間
    alternative_holiday = db.session.get(RecordPaidHoliday, staff_id)
    paid_holiday_time = alternative_holiday.BASETIMES_PAIDHOLIDAY

    for (
        one_person_attendance,
        job_contract,
        holiday_contract,
        work_time,
    ) in group_data_list:
        # DBの、入職日から契約休暇（D_HOLIDAY_HISTORY.START_DAY）まで間があるため
        contract_holiday_time = (
            paid_holiday_time
            if holiday_contract is None
            else holiday_contract.HOLIDAY_TIME
        )

        on_call_holiday_cnt += (
            1
            if one_person_attendance.ONCALL != "0"
            and one_person_attendance.WORKDAY.weekday() in [5, 6]
            else 0
        )
        on_call_cnt += (
            1
            if one_person_attendance.ONCALL != "0"
            and one_person_attendance.WORKDAY.weekday() not in [5, 6]
            else 0
        )
        on_call_correspond_cnt += (
            int(one_person_attendance.ONCALL_COUNT)
            if not isinstance(one_person_attendance.ONCALL_COUNT, type(None))
            and one_person_attendance.ONCALL_COUNT != ""
            and one_person_attendance.ONCALL_COUNT != "0"
            else 0
        )
        engel_correspond_cnt += (
            int(one_person_attendance.ENGEL_COUNT)
            if not isinstance(one_person_attendance.ENGEL_COUNT, type(None))
            and one_person_attendance.ENGEL_COUNT != ""
            and one_person_attendance.ENGEL_COUNT != "0"
            else 0
        )
        distance_sum += (
            float(one_person_attendance.MILEAGE)
            if not isinstance(one_person_attendance.MILEAGE, type(None))
            and one_person_attendance.MILEAGE != ""
            and one_person_attendance.MILEAGE != "0.0"
            else 0
        )
        # print(
        #     f"Inner Count log: {on_call_cnt} {on_call_cnt_cnt} {on_call_holiday_cnt} {engel_int_cnt}"
        # )

        holiday_cnt += 1 if one_person_attendance.NOTIFICATION == "3" else 0
        half_holiday_cnt += (
            1
            if one_person_attendance.NOTIFICATION == "4"
            or one_person_attendance.NOTIFICATION2 == "4"
            else 0
        )
        late_cnt += (
            1
            if one_person_attendance.NOTIFICATION == "1"
            or one_person_attendance.NOTIFICATION2 == "1"
            else 0
        )
        leave_early_cnt += (
            1
            if one_person_attendance.NOTIFICATION == "2"
            or one_person_attendance.NOTIFICATION2 == "2"
            else 0
        )
        absence_cnt += 1 if one_person_attendance.NOTIFICATION in n_absence_list else 0
        trip_cnt += 1 if one_person_attendance.NOTIFICATION == "5" else 0
        half_trip_cnt += (
            1
            if one_person_attendance.NOTIFICATION == "6"
            or one_person_attendance.NOTIFICATION2 == "6"
            else 0
        )
        reflesh_cnt += 1 if one_person_attendance.NOTIFICATION == "7" else 0
        # print(
        #     f"Inner Count log: {holiday_cnt} {half_holiday_cnt} {late_cnt} {leave_early_cnt} {absence_cnt} {trip_cnt} {half_trip_cnt}"
        # )

        real_time_append = real_work_times.append
        over_time_append = over_times.append
        nurse_holiday_work_append = nurse_holiday_works.append

        # print(f"ID{one_person_attendance.STAFFID} pass")
        # if one_person_attendance is None:
        #     raise TypeError(
        #         f"ID{one_person_attendance.STAFFID}: 勤務実績がまだありません"
        #     )

        if job_contract.CONTRACT_CODE != 2:
            setting_time.set_data(
                work_time,
                work_time,
                one_person_attendance.STARTTIME,
                one_person_attendance.ENDTIME,
                (
                    one_person_attendance.NOTIFICATION,
                    one_person_attendance.NOTIFICATION2,
                ),
                one_person_attendance.OVERTIME,
                one_person_attendance.HOLIDAY,
            )
        else:
            error_message = f"ID{staff_id} のD_HOLIDAY_HISTORYテーブル、及びM_RECORD_PAIDHOLIDAY.BASETIMES_PAIDHOLIDAYの値を確認してください"
            # 代替数値、変更の可能性あり
            alter_work_time = (
                paid_holiday_time
                if job_contract.PART_WORKTIME is None
                else job_contract.PART_WORKTIME
            )
            if job_contract.CONTRACT_CODE == 2 and holiday_contract is None:
                if paid_holiday_time is None or paid_holiday_time == 0:
                    raise IndexError(error_message)

            setting_time.set_data(
                alter_work_time,
                contract_holiday_time,
                one_person_attendance.STARTTIME,
                one_person_attendance.ENDTIME,
                (
                    one_person_attendance.NOTIFICATION,
                    one_person_attendance.NOTIFICATION2,
                ),
                one_person_attendance.OVERTIME,
                one_person_attendance.HOLIDAY,
            )

        print(f"ID: {one_person_attendance.STAFFID}")
        actual_work_time = setting_time.get_actual_work_time()
        calc_real_time = setting_time.get_real_time()
        over_time = setting_time.get_over_time()
        nurse_holiday_work_time = setting_time.calc_nurse_holiday_work()
        # except TypeError as e:
        #     msg = f"{e}: {one_person_attendance.STAFFID}"
        #     return render_template(
        #         "error/403.html", title="Exception message", message=msg
        #     )
        # else:

        # real_work_times.append(calc_real_time)
        real_time_append(calc_real_time)
        if one_person_attendance.OVERTIME == "1" and job_contract.CONTRACT_CODE != 2:
            # over_times.append(over_time)
            over_time_append(over_time)
        if nurse_holiday_work_time != 9.99:
            # nurse_holiday_works.append(nurse_holiday_work_time)
            nurse_holiday_work_append(nurse_holiday_work_time)

        print(f"{one_person_attendance.WORKDAY}")
        # print(f"Real time: {calc_real_time}")
        # print(f"Actual time: {actual_work_time}")
        # print(f"Real time list: {real_work_times}")
        # print(f"Over time list: {over_times}")
        # print(f"Nurse holiday: {nurse_holiday_works}")

        actual_second = (
            actual_work_time.total_seconds()
            if actual_work_time > timedelta(hours=0)
            else 0.0
        )
        workday_count += 1 if actual_second != 0.0 else 0

        actual_time_sum += actual_second
        time_sum_normal = actual_time_sum / 3600
        # 【項目12】
        actual_time_rnd = Decimal(time_sum_normal).quantize(
            Decimal("0.01"), ROUND_HALF_UP
        )

        w_h = actual_time_sum // (60 * 60)
        w_m = (actual_time_sum - w_h * 60 * 60) // 60
        # 【項目11】
        actual_time60 = w_h + w_m / 100

        real_sum: int = sum(real_work_times)
        w_h = real_sum // (60 * 60)
        w_m = (real_sum - w_h * 60 * 60) // 60
        # 【項目13】
        real_time = w_h + w_m / 100
        # real_time_10 = real_sum / (60 * 60)

        over_sum: int = sum(over_times)
        o_h = over_sum // (60 * 60)
        o_m = (over_sum - o_h * 60 * 60) // 60
        # 【項目17】
        over60 = o_h + o_m / 100

        over10 = over_sum / (60 * 60)
        # 【項目18】
        over10_rnd = Decimal(over10).quantize(Decimal("0.01"), ROUND_HALF_UP)

        sum_nrs: int = sum(nurse_holiday_works)
        h_h = sum_nrs // (60 * 60)
        h_m = (sum_nrs - h_h * 60 * 60) // 60
        # 【項目22】
        holiday_work60 = h_h + h_m / 100

        holiday_work_10 = sum_nrs / (60 * 60)
        # 【項目23】
        holiday_work10_rnd = Decimal(holiday_work_10).quantize(
            Decimal("0.01"), ROUND_HALF_UP
        )

        sum_dict: Dict[str, int] = output_rest_time(
            one_person_attendance.NOTIFICATION, one_person_attendance.NOTIFICATION2
        )
        timeoff += sum_dict.get("Off")
        halfway_through += sum_dict.get("Through")

    """ ここ、2年遡りと違う """
    # if job_contract.CONTRACT_CODE != 2:
    #     disp_work_time, disp_holiday_time = work_time, work_time
    # else:
    #     disp_work_time, disp_holiday_time = (
    #         job_contract.PART_WORKTIME,
    #         contract_holiday_time,
    #     )

    result_series = pds(
        [
            # disp_work_time,
            # disp_holiday_time,
            job_contract.CONTRACT_CODE,
            on_call_cnt,
            on_call_holiday_cnt,
            on_call_correspond_cnt,
            engel_correspond_cnt,
            actual_time60,
            actual_time_rnd,
            real_time,
            workday_count,
            holiday_cnt,
            half_holiday_cnt,
            over60,
            over10_rnd,
            late_cnt,
            leave_early_cnt,
            absence_cnt,
            holiday_work60,
            holiday_work10_rnd,
            trip_cnt,
            half_trip_cnt,
            reflesh_cnt,
            distance_sum,
            timeoff,
            halfway_through,
        ],
        index=[
            # "契約労働（時間）",
            # "契約休暇（時間）",
            "契約形態",
            "オンコール平日担当回数",
            "オンコール土日担当回数",
            "オンコール対応件数",
            "エンゼルケア対応件数",
            "実働時間計",
            "実働時間計（１０進法）",
            "リアル実働時間",
            "実働日数",
            "年休（全日）",
            "年休（半日）",
            "時間外",
            "時間外（１０進法）",
            "遅刻",
            "早退",
            "欠勤",
            "祝日手当時間",
            "祝日手当時間（１０進法）",
            "出張（全日）",
            "出張（半日）",
            "リフレッシュ休暇",
            "走行距離",
            "時間休",
            "中抜け",
        ],
        name=one_person_attendance.WORKDAY,
    )

    return result_series
