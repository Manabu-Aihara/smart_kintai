import os
from dataclasses import dataclass

from skpy import Skype

from smtplib import SMTP

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from email.utils import formatdate

from dotenv import load_dotenv

load_dotenv()


def make_skype_object(skype_user: str, skype_password: str):
    # ここも暫定的、os.getenv(...)可変
    skype_obj = Skype(skype_user, skype_password)
    return skype_obj


# skypeの指定したグループにメッセージを送信(通知)する関数
# http://kakedashi-xx.com:25214/index.php/2021/04/08/post-2199/ を参照
# def ask_approval(user: str, password: str, message: str):
#     skype_obj = make_skype_object(user, password)
#     for c in skype_obj.chats.recent():
#         chat = skype_obj.chats[c]
#         if hasattr(chat, 'topic') and chat.topic == os.getenv("SKYPE_TOPIC"):
#             chat.sendMsg(message)
#             break
def make_system_skype_object():
    skype_provider = make_skype_object(
        os.getenv("SKYPE_ACCOUNT"), os.getenv("SYSTEM_PASS")
    )
    return skype_provider


@dataclass
class SkypeBaseException(Exception):
    skype_account: str


class SkypeRelatedException(SkypeBaseException):
    def __str__(self) -> str:
        return f"こちらのIDのSkypeIdがないか、無効です。: {super().__str__()}\n"


def check_skype_account(skype_liveId: str, manager_id: int):
    if skype_liveId is None:
        raise SkypeRelatedException(str(manager_id))


"""
    以下メール機能
    """


# 以下https://zenn.dev/shimakaze_soft/articles/9601818a95309c を参考
def createMIMEText(mail_from: str, mail_to: str, message: str):
    # MIMETextを作成
    # msg = MIMEText(message, "html")
    # msg = MIMEText(message)
    msg = MIMEText(message, "plain", "utf-8")

    msg["Subject"] = "所属長からのコメント"
    msg["From"] = mail_from
    msg["To"] = mail_to
    msg["Date"] = formatdate()

    return msg


def set_smtp(account: str, password: str, mail_text_func: MIMEText):
    host = os.getenv("OUTLOOK_HOST")
    # Literal[587]型なので注意
    # port = 587

    server = SMTP(host, 587)
    # server.connect()
    server.starttls()
    server.login(account, password)

    server.send_message(mail_text_func)

    server.quit()


"""
    メール送信機能
    Param:
        source: str 送信元
        destination: str 宛先
        password: str 送信者パスワード
        message: str メッセージ
        smtp_config_func: None メール設定、送信関数
    """


def send_mail(
    source: str,
    destination: str,
    password: str,
    message: str,
    smtp_config_func: None = set_smtp,
):
    mime_message = createMIMEText(source, destination, message)
    smtp_config_func(source, password, mime_message)
