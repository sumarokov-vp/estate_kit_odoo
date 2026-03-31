from typing import Any, Callable


class OdooMatchWriter:
    def __init__(self, raw_write: Callable) -> None:
        self._raw_write = raw_write

    def write(self, record: Any, vals: dict[str, Any]) -> bool:
        return self._raw_write(record, vals)
