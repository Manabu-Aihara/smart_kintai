import logging
from datetime import datetime


class AttendanceLogger:
    @staticmethod
    def get_logger(touch_month: int, level: str = "INFO"):
        # getLoggerにモジュール名を与える
        logger = logging.getLogger(__name__)
        # loggingの多重実行を防止する
        # https://qiita.com/thistle_/items/f9042ca94f28f2cbfd9e
        for h in logger.handlers[:]:
            logger.removeHandler(h)
            h.close()

        # これを設定しておかないと後のsetLevelでDEBUG以下を指定しても効かないっぽい
        level: int = getattr(logging, level)
        logger.setLevel(level)

        # 出力先を指定している
        date_now = datetime.now()
        logfile = f"attendance{date_now.year}{touch_month}.csv"
        handler = logging.FileHandler(logfile)

        # そのハンドラの対象のレベルを設定する
        handler.setLevel(level)

        # どんなフォーマットにするかを指定する。公式に使える変数は書いてますね。
        formatter = logging.Formatter("%(asctime)s,%(message)s")
        handler.setFormatter(formatter)

        # 設定したハンドラをloggerに適用している
        logger.addHandler(handler)

        return logger
