"""Stub server.env.mixin for Odoo 19.

This is a minimal implementation that provides the mixin interface
without the actual environment configuration functionality.
All fields are editable through the Odoo UI.
"""
from odoo import api, models

from odoo.addons.base_sparse_field.models.fields import Serialized


class ServerEnvMixin(models.AbstractModel):
    """Minimal stub of server.env.mixin for Odoo 19."""

    _name = "server.env.mixin"
    _description = "Server Environment Mixin (Stub)"

    server_env_defaults = Serialized()

    @property
    def _server_env_fields(self):
        """Dict of fields from environment config. Override in inheriting models."""
        return {}

    @api.model
    def _server_env_global_section_name(self):
        """Name of the global section in the configuration files."""
        return self._name.replace(".", "_")

    _server_env_section_name_field = "name"

    def _server_env_section_name(self):
        """Name of the section in the configuration files."""
        self.ensure_one()
        val = self[self._server_env_section_name_field]
        if not val:
            return
        base = self._server_env_global_section_name()
        return ".".join((base, val))
