from typing import Dict, List
import requests
import re

from flask import jsonify, make_response

from . import app
from .carry_over_lib import calculate_carry_over_all, calculate_prev_carry


def retrieve_api_data(url: str) -> List[dict]:
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

    return result


@app.route("/carry-over/<shozoku_code>", methods=["GET"])
def get_carry_over(shozoku_code):
    data_url = f"http://0.0.0.0:8001/frame-data/{shozoku_code}"
    prev_data_url = f"http://0.0.0.0:8001/frame-prev-data/{shozoku_code}"
    try:
        two_years_data_dict = retrieve_api_data(data_url)
        prev_data_dict = retrieve_api_data(prev_data_url)

        base_dict_result = calculate_carry_over_all(two_years_data_dict)
        prev_dict_result = calculate_prev_carry(prev_data_dict)
        # if base_dict_result is None:
        #     base_dict_result = {}
        # if prev_dict_result is None:
        #     prev_dict_result = {}
        return jsonify(base_dict_result, prev_dict_result)
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500
