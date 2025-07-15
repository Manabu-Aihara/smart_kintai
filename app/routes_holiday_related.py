import requests
from flask import jsonify

from . import app


@app.route("/get-member-leave/<shozoku_code>")
def get_member_leave(shozoku_code):
    url = f"http://127.0.0.1:8001/frame-data/{shozoku_code}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        api_data = response.json()  # dict形式で取得

        members = api_data.get("members", [])
        result = []
        for member in members:
            # 必要な項目だけ抽出
            extracted = {
                # "name": member.get("name"),
                "workday_count": member.get("実働日数"),
                "annual_leave_full": member.get("年休（全日）"),
                "annual_leave_half": member.get("年休（半日）"),
                "hourly_leave": member.get("時間休"),
                "half_hour_leave": member.get("中抜け"),
            }
            result.append(extracted)

        return jsonify(result)
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500
