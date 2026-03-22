from typing import Any

from odoo import api as api
from odoo import fields as fields
from odoo import http as http
from odoo import models as models

SUPERUSER_ID: int

def _(source: str, *args: Any, **kwargs: Any) -> str: ...
