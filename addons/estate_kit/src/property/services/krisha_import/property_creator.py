from typing import Any

from .protocols import IFieldMapper


class PropertyCreator:
    def __init__(self, env, field_mapper: IFieldMapper) -> None:
        self._env = env
        self._field_mapper = field_mapper

    def create(self, detail: dict[str, Any]) -> int:
        vals = self._field_mapper.map(detail)
        record = self._env["estate.property"].with_context(allow_empty_address=True).create(vals)
        return record.id
