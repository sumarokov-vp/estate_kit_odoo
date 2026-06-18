from datetime import date

from ..address.service import AddressService

_MONTHS_GENITIVE = {
    1: "января",
    2: "февраля",
    3: "марта",
    4: "апреля",
    5: "мая",
    6: "июня",
    7: "июля",
    8: "августа",
    9: "сентября",
    10: "октября",
    11: "ноября",
    12: "декабря",
}

_PROPERTY_KIND = {
    "apartment": "квартира",
    "house": "жилой дом с земельным участком",
    "townhouse": "таунхаус",
    "commercial": "коммерческая недвижимость",
    "land": "земельный участок",
}

_DEFAULT_PLACE = "г. Алматы"
_DEFAULT_PROTECTION_MONTHS = "шести"


class ContractDataService:
    def __init__(self, env) -> None:
        self._env = env

    def build(self, record) -> dict:
        record.ensure_one()
        return {
            "number": _s(record.contract_number),
            "place": _DEFAULT_PLACE,
            "date": self._date_parts(record.contract_start or date.today()),
            "end_date": self._date_parts(record.contract_end),
            "exclusive": record.contract_type == "exclusive",
            "fee_percent": self._fee_percent(record),
            "protection_months": _DEFAULT_PROTECTION_MONTHS,
            "executor": self._executor(),
            "customer": self._customer(record),
            "object": self._object(record),
        }

    def _date_parts(self, value) -> dict:
        if not value:
            return {"day": "", "month": "", "year": ""}
        return {
            "day": str(value.day),
            "month": _MONTHS_GENITIVE.get(value.month, ""),
            "year": str(value.year),
        }

    def _fee_percent(self, record) -> str:
        if not record.min_commission_percent:
            return ""
        return _trim_number(f"{record.min_commission_percent:.2f}")

    def _executor(self) -> dict:
        params = self._env["ir.config_parameter"].sudo()
        # TODO (точка расширения): bin/iik/bik/bank/address/director/director_full
        # будут заполняться из реквизитов организации CRM (res.company / профиль агентства).
        # Пока система их не хранит — отдаём пустые строки, шаблон отрисует пустой бланк.
        return {
            "name": _s(params.get_param("estate_kit.reg_company_name")),
            "bin": "",
            "director": "",
            "director_full": "",
            "iik": "",
            "bik": "",
            "bank": "",
            "address": "",
            "phone": _s(params.get_param("estate_kit.reg_phone")),
        }

    def _customer(self, record) -> dict:
        partner = record.owner_id
        is_legal = bool(partner and partner.is_company)
        return {
            "is_legal": is_legal,
            "name": _s(partner.name if partner else None) or _s(record.owner_name),
            "iin": "" if is_legal else _s(partner.vat if partner else None),
            "passport": "",
            "bin": _s(partner.vat if partner else None) if is_legal else "",
            "iik": "",
            "bank": "",
            "address": self._partner_address(partner),
            "phone": _s(record.owner_phone) or _s(record.owner_phone_raw),
            "signatory": _s(partner.name if partner else None) or _s(record.owner_name),
        }

    def _partner_address(self, partner) -> str:
        if not partner:
            return ""
        parts = [partner.street, partner.street2, partner.city]
        return ", ".join(part for part in parts if part)

    def _object(self, record) -> dict:
        # TODO (точка расширения): title_doc/title_doc_date/title_doc_no/state/
        # encumbrance_text появятся из EAV-атрибутов позже. Пока пустые строки.
        return {
            "kind": _PROPERTY_KIND.get(record.property_type, ""),
            "address": ", ".join(AddressService.build_parts(record, include_district=True)),
            "title_doc": "",
            "title_doc_date": "",
            "title_doc_no": "",
            "area_total": _format_area(record.area_total),
            "area_land": _format_area(record.area_land),
            "state": "",
            "price_text": _format_price(record.price or record.listing_price),
            "encumbrance": bool(record.encumbrance or record.is_pledged),
            "encumbrance_text": "",
        }


def _s(value) -> str:
    return str(value) if value else ""


def _trim_number(text: str) -> str:
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def _format_area(value) -> str:
    if not value:
        return ""
    return _trim_number(f"{value:.2f}").replace(".", ",")


def _format_price(value) -> str:
    if not value:
        return ""
    integer = int(round(value))
    grouped = f"{integer:,}".replace(",", " ")
    return grouped
