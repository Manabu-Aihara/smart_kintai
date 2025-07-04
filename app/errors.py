from flask import render_template
from flask_login import current_user

from app import app, db


"""***** 閲覧者へのerror表示 *****"""


@app.errorhandler(404)
def page_not_found(error):
    return (
        render_template(
            "error/404.html",
            title="The requested URL was Not found",
            message="アクセスしていただいたURLが見つかりません。",
        ),
        404,
    )


@app.errorhandler(500)
def system_error(error):  # error.descriptionでエラー時の文字列取得
    return render_template("error/500.html", title="500 Sysstem Error"), 500


@app.errorhandler(403)
# def not_admin(error):
#     return (
#         render_template("error/403.html", title="inhibition", message="アクセス権限がありません。"),
#         403,
#     )
def not_admin():
    return (
        render_template(
            "error/403.html",
            title="inhibition",
            message="アクセス権限がありません。",
            u=current_user,
        ),
        403,
    )


"""
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
"""
