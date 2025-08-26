from typing import List

from sqlalchemy import update, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.database_async import get_session
from app.models import TableOfCount
from app.select_only_sync import read_session, get_sync_record


async def get_query_from_date(year_and_month: str) -> List[TableOfCount]:
    counter_data_list = (
        read_session.query(TableOfCount)
        .filter(TableOfCount.YEAR_MONTH == year_and_month)
        .all()
    )
    # result_query_list = []
    # for counter_data in counter_data_list:
    #     result_query_list.append(counter_data)

    return counter_data_list


async def merge_count_table(count_table_obj: TableOfCount, count_table_id: str) -> None:
    # making_id = f"{count_table_obj.YEAR_MONTH}-{start_day}-{count_table_obj.STAFFID}-{count_table_obj.CONTRACT_CODE}"

    # 今読み込む側 local_cat_db -> panda?
    # select_stmt = select(TableOfCount).filter(TableOfCount.id == making_id)
    # target_data: Optional[TableOfCount]
    # async with get_session() as session:
    #     # こっちでも良かった
    #     # target_data = session.get(TableOfCount, making_id)
    #     query_result = await session.execute(statement=select_stmt)
    #     target_data = query_result.scalar_one_or_none()
    target_data = get_sync_record(count_table_id)

    if count_table_obj.__dict__.get("_sa_instance_state"):
        object_dict = count_table_obj.__dict__.pop("_sa_instance_state")
        print(object_dict)

    if target_data is not None:
        # 今度、書き込む側 panda
        print("☆書き込む側 panda")
        stmt = (
            update(TableOfCount)
            .where(TableOfCount.id == count_table_id)
            .values(count_table_obj.__dict__)
        )
    else:  # TableOfCount is None
        print("☆TableOfCount is None")
        stmt = insert(TableOfCount).values(count_table_obj.__dict__)

    try:
        async with get_session() as session:
            async with session.begin():
                await session.execute(statement=stmt)
    # except IntegrityError as ie:
    #     print(ie)
    except TypeError as te:
        raise "再度「再集計」ボタンをクリックしてください"
