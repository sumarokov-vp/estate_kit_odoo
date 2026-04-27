from odoo import http
from odoo.http import Response, request

_VISIBLE_STAGE_CODES = ("new", "viewed", "selected")


class LeadMatchesController(http.Controller):

    @http.route(
        "/estate_kit/leads/<string:token>",
        type="http",
        auth="none",
        methods=["GET"],
        csrf=False,
    )
    def lead_matches_page(self, token):
        lead = self._get_lead(token)
        if not lead:
            return request.not_found()

        items = self._collect_items(lead)
        company_name, company_logo = self._company_info()
        values = {
            "lead": lead,
            "items": items,
            "company_name": company_name,
            "company_logo": company_logo,
        }
        html = request.env["ir.qweb"]._render(
            "estate_kit.lead_matches_public_page", values
        )
        return Response(
            "<!DOCTYPE html>\n" + str(html),
            content_type="text/html; charset=utf-8",
        )

    @staticmethod
    def _get_lead(token):
        return (
            request.env["crm.lead"]
            .sudo()
            .search([("lead_code", "=", token)], limit=1)
        )

    @classmethod
    def _collect_items(cls, lead):
        matches = lead.match_ids.filtered(
            lambda m: m.stage_id and m.stage_id.code in _VISIBLE_STAGE_CODES
        )
        token_model = request.env["estate.property.public.view.token"].sudo()
        items = []
        for match in matches:
            prop = match.property_id
            if not prop:
                continue
            public_url = token_model.get_or_create_url(prop.id)
            token = public_url.rsplit("/", 1)[-1] if public_url else None
            items.append(
                {
                    "name": prop.name or "Объект недвижимости",
                    "url": public_url or "#",
                    "price_text": cls._format_price(prop),
                    "address": cls._build_address(prop),
                    "specs": cls._build_specs(prop),
                    "thumb_url": cls._main_thumb_url(prop, token),
                }
            )
        return items

    @staticmethod
    def _format_price(prop):
        if not prop.price:
            return ""
        symbol = prop.currency_id.symbol or ""
        position = prop.currency_id.position or "after"
        amount = f"{prop.price:,.0f}".replace(",", " ")
        if position == "before":
            return f"{symbol} {amount}".strip()
        return f"{amount} {symbol}".strip()

    @staticmethod
    def _build_address(prop):
        parts = []
        if prop.city_id:
            parts.append(prop.city_id.name)
        if prop.district_id:
            parts.append(prop.district_id.name)
        if prop.street_id:
            parts.append(prop.street_id.name)
        if prop.house_number:
            parts.append(prop.house_number)
        return ", ".join(p for p in parts if p)

    @staticmethod
    def _build_specs(prop):
        specs = []
        if prop.rooms:
            specs.append(f"{prop.rooms}-комн.")
        if prop.area_total:
            specs.append(f"{prop.area_total:g} м²")
        if prop.floor or prop.floors_total:
            floor = prop.floor or "—"
            total = prop.floors_total or "—"
            specs.append(f"{floor}/{total} эт.")
        return " · ".join(specs)

    @staticmethod
    def _main_thumb_url(prop, token):
        if not token:
            return None
        images = prop.image_ids.sorted(
            key=lambda i: (-1000 if i.is_main else 0, i.sequence, i.id)
        )
        if not images:
            return None
        return f"/estate_kit/view/{token}/thumb/{images[0].id}"

    @staticmethod
    def _company_info():
        company = request.env["res.company"].sudo().search([], limit=1)
        if not company:
            return "Estate Kit", None
        raw = company.logo_web or company.logo
        logo = None
        if raw:
            b64 = raw.decode("ascii") if isinstance(raw, bytes) else raw
            logo = f"data:image/png;base64,{b64}"
        return company.name, logo
