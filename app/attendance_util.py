from typing import Tuple, TypeVar, Any, List, Dict
from datetime import datetime
import re
import pandas as pd

from . import db
from .models import Department, Contract, Post, Team, JobType


def get_month_workday(selected_date: str) -> Tuple[int, int]:
    if selected_date:
        select_year = datetime.strptime(selected_date, "%Y-%m").year
        select_month = datetime.strptime(selected_date, "%Y-%m").month
        # session["workday_data"] = selected_date
        # workday_date = session["workday_data"]
    else:
        select_year = datetime.today().year
        select_month = datetime.today().month
        # workday_date = datetime.today().strftime("%Y-%m")

    return (
        select_year,
        select_month,
    )


"""
    @Params:
        query_name: 実質返すクエリーのカラム名
        table_code: int DBテーブルコード
        user_code: int User内コード
    @Return:
        result_query: Any DBテーブルコードから返す名称
        """


def get_user_role(query_name, table_code: int, user_code: int = 0) -> Any:
    result_query = db.session.query(query_name).filter(table_code == user_code).first()
    if result_query is None:
        # リスト対応させるため、空の場合は空文字を返す
        result_query = ""
        return result_query
    else:
        return result_query[0]


T = TypeVar("T")


def convert_null_role(db_obj: T) -> T:
    disp_department = get_user_role(
        Department.NAME, Department.CODE, db_obj.DEPARTMENT_CODE
    )
    disp_team = get_user_role(Team.SHORTNAME, Team.CODE, db_obj.TEAM_CODE)
    disp_contract = get_user_role(
        Contract.NAME, Contract.CONTRACT_CODE, db_obj.CONTRACT_CODE
    )
    disp_JobType = get_user_role(
        JobType.SHORTNAME, JobType.JOBTYPE_CODE, db_obj.JOBTYPE_CODE
    )
    disp_post = get_user_role(Post.NAME, Post.CODE, db_obj.POST_CODE)

    db_obj.department = disp_department
    db_obj.team = disp_team
    db_obj.contract = disp_contract
    db_obj.job_type = disp_JobType
    db_obj.post = disp_post
    return db_obj


def check_table_member(staff_id: int, table_model: T):
    neccesary_object = db.session.get(table_model, staff_id)
    object_attributes = [n for n in neccesary_object.__dict__]
    attr_list = []
    for neccesary_attr in object_attributes[1:]:
        attribute_value = getattr(neccesary_object, neccesary_attr)
        if attribute_value is None or attribute_value == "":
            attr_list.append(neccesary_attr)
            # raise ValueError(f"There is not {neccesary_attr} value of {staff_id}")
    if len(attr_list) != 0:
        return attr_list
    else:
        return "無問題"


# Pythonの実行速度を測定(プロファイル)
# https://zenn.dev/timoneko/articles/16f9ee7113f3cd


def convert_ym_date(touched_date: str) -> Tuple[str, int]:
    the_year = re.sub(r"(\d{4})-(\d{2})", r"\1", touched_date)
    the_month = re.sub(r"(\d{4})-(\d{2})", r"\2", touched_date)
    # 01を1にしなければならない
    return the_year, int(the_month)


"""
    @Params:
        : str 指定した年月
    @Return:
        : list<dict> スタッフ、最終更新日時のペア
        """


def extract_last_update(selected_date: str) -> List[Dict]:
    touched_year, touched_month = convert_ym_date(selected_date)
    csv_file = f"attendance{touched_year}{touched_month}.csv"

    df = pd.read_csv(csv_file, names=["Date", "ms", "Staff"])
    # Staffの重複を消す
    df_no_duplicate = df.drop_duplicates(subset=["Staff"], keep="last")

    the_dict_list: List[Dict] = [{}]
    # 値の抽出
    staffs = df_no_duplicate.loc[:, "Staff"]
    last_dates = df_no_duplicate.loc[:, "Date"]
    for m, n in zip(staffs.to_list(), last_dates.to_list()):
        the_dict_list.append({"staff": m, "last_date": n})

    return the_dict_list
