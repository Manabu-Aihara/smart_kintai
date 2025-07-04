from typing import Tuple

from app import app, db
from app.common_func import GetPullDownList
from app.models import Busho, Team, KinmuTaisei, Jobtype, Post


def get_pulldown_list() -> Tuple[list]:
    with app.app_context():
        db.create_all()
        department_opt = GetPullDownList(Busho, Busho.CODE, Busho.NAME, Busho.CODE)
        team_opt = GetPullDownList(Team, Team.CODE, Team.NAME, Team.CODE)
        contract_opt = GetPullDownList(
            KinmuTaisei,
            KinmuTaisei.CONTRACT_CODE,
            KinmuTaisei.NAME,
            KinmuTaisei.CONTRACT_CODE,
        )
        jobtype_opt = GetPullDownList(
            Jobtype, Jobtype.JOBTYPE_CODE, Jobtype.NAME, Jobtype.JOBTYPE_CODE
        )
        post_code_opt = GetPullDownList(Post, Post.CODE, Post.NAME, Post.CODE)
        return department_opt, team_opt, contract_opt, jobtype_opt, post_code_opt
