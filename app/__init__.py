import os
from datetime import timedelta, date
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_bcrypt import Bcrypt

from jinja2 import Environment
from types import SimpleNamespace

from config import Config

# loggerを定義
logger = logging.getLogger(__name__)

# loggerのログレベルを設定
logger.setLevel(logging.WARNING)

# loggerのフォーマット、出力先ファイルを定義
formatter = logging.Formatter("%(asctime)s - %(levelname)s:%(name)s - %(message)s")
file_handler = logging.FileHandler("test.log")
file_handler.setFormatter(formatter)

# loggerのフォーマット、出力先ファイルを設定
logger.addHandler(file_handler)

logger.warning("warning")
logger.error("error", exc_info=True)


LOGFILE_NAME = "DEBUG.log"

app = Flask(__name__)

# 日本語文字化け対応
app.json.ensure_ascii = False

app.config.update(
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=360),
)

# ここをモック化できないだろうか
app.config.from_object(Config)

db = SQLAlchemy(app)
MIGRATE = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = "login"
bootstrap = Bootstrap(app)
moment = Moment(app)
bcrypt = Bcrypt(app)

jinja_env = Environment(extensions=["jinja2.ext.i18n"])
app.jinja_env.add_extension("jinja2.ext.loopcontrols")

app.logger.setLevel(logging.DEBUG)
log_handler = logging.FileHandler(LOGFILE_NAME)
log_handler.setLevel(logging.DEBUG)
app.logger.addHandler(log_handler)


@app.context_processor
def inject_stf_login():
    """全テンプレートに stf_login を注入する。

    - ログイン済み: current_user をそのまま渡す
    - 未ログイン: ADMIN=False のダミーを渡す
    """
    try:
        if getattr(current_user, "is_authenticated", False):
            return {"stf_login": current_user}
    except Exception:
        pass
    non_admin = SimpleNamespace(ADMIN=False)
    return {"stf_login": non_admin}


from app import routes, models, errors  # noqa: E402,F401
from app import routes_sub  # noqa: E402,F401


if not os.path.exists("logs"):
    os.mkdir("logs")
file_handler = RotatingFileHandler("logs/dakoku.log", maxBytes=10240, backupCount=10)
file_handler.setFormatter(
    logging.Formatter(
        "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)s]"
    )
)
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)

app.logger.setLevel(logging.INFO)

from .routes_holiday_related import excute_scheduler_alert_method  # noqa: E402,F401

today = date.today()
if today.month == 3:
    excute_scheduler_alert_method("4")
elif today.month == 9:
    excute_scheduler_alert_method("10")
