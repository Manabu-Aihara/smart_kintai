import requests
import re

from flask import jsonify, make_response

from . import app
from .carry_over_lib import calculate_carry_over_all
from .holiday_logging import HolidayLogger


@app.route("/carry-over/<shozoku_code>", methods=["GET"])
def get_carry_over(shozoku_code):
    url = f"http://0.0.0.0:8001/frame-data/{shozoku_code}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        api_data_dict = response.json()  # dict形式（この時点で）で取得

        result = []
        for key, item in api_data_dict.items():
            staff_id: str = re.sub(r"(\d{1,4}): (.+)", r"\1", key)
            print(f"Staff ID: {staff_id} / item: {item}")
            extracted = {
                "staff_id": int(staff_id),
                "contract_vacation_hours": item.get("契約休暇（時間）"),
                "leave_full": item.get("年休（全日）"),
                "leave_half": item.get("年休（半日）"),
                "hourly_leave": item.get("時間休"),
                "half_hour_leave": item.get("中抜け"),
            }
            result.append(extracted)

        carry_over_data = calculate_carry_over_all(result)
        return make_response(jsonify(carry_over_data))
        # return jsonify(carry_over_data)
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500
