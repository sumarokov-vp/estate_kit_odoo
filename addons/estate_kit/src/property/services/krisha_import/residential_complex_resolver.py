import logging

_logger = logging.getLogger(__name__)


class ResidentialComplexResolver:
    def __init__(self, env) -> None:
        self._env = env

    def resolve(
        self,
        krisha_complex_id: int | None,
        name: str | None,
        krisha_url: str | None,
        city_id: int | None,
    ) -> int | None:
        model = self._env["estate.residential.complex"]

        if krisha_complex_id:
            record = model.search(
                [("krisha_complex_id", "=", krisha_complex_id)], limit=1
            )
            if record:
                updates: dict = {}
                if name and not record.name:
                    updates["name"] = name
                if name and record.name != name:
                    updates["name"] = name
                if krisha_url and not record.krisha_url:
                    updates["krisha_url"] = krisha_url
                if city_id and not record.city_id:
                    updates["city_id"] = city_id
                if updates:
                    record.write(updates)
                return record.id

        if name:
            domain: list[tuple[str, str, str | int]] = [("name", "=ilike", name)]
            if city_id:
                domain.append(("city_id", "=", city_id))
            record = model.search(domain, limit=1)
            if record:
                updates = {}
                if krisha_complex_id and not record.krisha_complex_id:
                    updates["krisha_complex_id"] = krisha_complex_id
                if krisha_url and not record.krisha_url:
                    updates["krisha_url"] = krisha_url
                if updates:
                    record.write(updates)
                return record.id

        if not name and not krisha_complex_id:
            return None

        record = model.create({
            "name": name or f"ЖК #{krisha_complex_id}",
            "krisha_complex_id": krisha_complex_id or 0,
            "krisha_url": krisha_url or False,
            "city_id": city_id or False,
        })
        _logger.info("Created residential complex %s (krisha_id=%s)", record.name, krisha_complex_id)
        return record.id
