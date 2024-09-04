from __future__ import annotations
import os
from typing import Any, Tuple

from airflow.hooks.base import BaseHook
from servicefoundry.lib.const import API_KEY_ENV_NAME, HOST_ENV_NAME


class TrueFoundryHook(BaseHook):
    conn_name_attr = "truefoundry_conn_id"
    default_conn_name = "truefoundry_default"
    conn_type = "truefoundry"
    hook_name = "TrueFoundry"

    @staticmethod
    def get_connection_form_widgets() -> dict[str, Any]:
        """Returns connection widgets to add to connection form"""
        from flask_appbuilder.fieldwidgets import BS3PasswordFieldWidget
        from flask_babel import lazy_gettext
        from wtforms import PasswordField

        return {
            "token": PasswordField(lazy_gettext("Token"), widget=BS3PasswordFieldWidget())
        }

    @staticmethod
    def get_ui_field_behaviour() -> dict:
        """Returns custom field behaviour"""
        return {
            "hidden_fields": ["port", "password", "login", "schema", "extra"],
            "relabeling": {},
            "placeholders": {
                "host": "https://truefoundry.com/",
                "token": "mY53cr3tk3y!"
            },
        }

    def __init__(
            self,
            truefoundry_conn_id: str = default_conn_name
    ) -> None:
        super().__init__()
        self.truefoundry_conn_id = truefoundry_conn_id
        self.host = None
        self.token = None

    def get_conn(self):
        conn = self.get_connection(self.truefoundry_conn_id)
        self.host = conn.host
        self.token = conn.extra_dejson["token"]
        os.environ[
            API_KEY_ENV_NAME] = self.token
        os.environ[HOST_ENV_NAME] = self.host

        return self

    def test_connection(self) -> Tuple[bool, str]:
        """Test a connection"""
        try:
            self.get_conn()
            # TODO - make a health check call to verify if token and host are valid
            return True, "Connection successfully tested"
        except Exception as e:
            return False, str(e)
