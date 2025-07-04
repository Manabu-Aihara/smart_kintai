from app import app

from app.holiday_subject import SubjectImpl
from app.holiday_observer import ObserverRegist, ObserverCarry, ObserverCheckType


def execute_observer():
    # if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
    print("Re-start!")

    """
        2024/4/2 年休付与オブザーバー追加
        """
    subject = SubjectImpl()
    observer_type = ObserverCheckType()
    observer_carry = ObserverCarry()
    observer_regist = ObserverRegist()
    subject.attach(observer_type)
    subject.attach(observer_carry)
    subject.attach(observer_regist)

    # with app.app_context():
    #     subject.execute()

    subject.detach(observer_type)
    subject.detach(observer_carry)
    subject.detach(observer_regist)
