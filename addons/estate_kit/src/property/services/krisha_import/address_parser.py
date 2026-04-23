import re

_DROP_PREFIXES = frozenset({
    "мкр",
    "мкр.",
    "микрорайон",
    "район",
    "р-н",
    "г",
    "г.",
    "город",
    "пос",
    "пос.",
    "посёлок",
    "село",
    "с.",
})

_STRIP_PREFIXES = frozenset({
    "ул",
    "ул.",
    "улица",
    "пр",
    "пр.",
    "проспект",
})

_HOUSE_TAIL_RE = re.compile(r"^(?P<street>.+?)\s+(?P<house>\d+[A-Za-zА-Яа-я0-9/\-]*)$")


class AddressParser:
    def parse(self, address_title: str) -> tuple[str | None, str | None]:
        if not address_title or not isinstance(address_title, str):
            return None, None

        parts = [p.strip() for p in address_title.split(",") if p.strip()]
        candidate: str | None = None
        for part in parts:
            tokens = part.split()
            if not tokens:
                continue
            first = tokens[0].lower()
            if first in _DROP_PREFIXES:
                continue
            if first in _STRIP_PREFIXES:
                remainder = " ".join(tokens[1:]).strip()
                if remainder:
                    candidate = remainder
                    break
                continue
            candidate = part
            break

        if candidate is None:
            return None, None

        match = _HOUSE_TAIL_RE.match(candidate)
        if match:
            street = match.group("street").strip() or None
            house = match.group("house").strip() or None
            return street, house

        return candidate, None
