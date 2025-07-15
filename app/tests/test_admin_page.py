import pytest
from typing import OrderedDict

from app.forms import AddDataUserForm


# @pytest.mark.skip
def test_user_form_item(request_context, db_session):
    user_form = AddDataUserForm()
    for form_key, form_value in user_form.__dict__.items():
        if isinstance(form_value, OrderedDict):
            for key, value in form_value.items():
                print(f"Ordered dict: {key}")
