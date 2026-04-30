"""Test quick create form: fill fields, click Add, capture errors."""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import BrowserSession, SCREENSHOTS_DIR


def run():
    errors = []
    responses = []

    with BrowserSession() as s:
        page = s.page

        page.on("console", lambda msg: errors.append(f"[{msg.type}] {msg.text}") if msg.type in ("error", "warning") else None)
        page.on("pageerror", lambda err: errors.append(f"[PAGE ERROR] {err}"))

        def on_response(response):
            if "call_kw" in response.url or "call_button" in response.url:
                try:
                    body = response.json()
                    if "error" in body:
                        responses.append({"url": response.url[-60:], "error": body["error"]})
                except Exception:
                    pass

        page.on("response", on_response)

        # Go to CRM kanban
        s.goto("/odoo/crm")
        page.wait_for_timeout(2000)

        # Remove "Моя воронка" filter if present
        try:
            page.click(".o_facet_remove", timeout=2000)
            page.wait_for_timeout(1500)
        except Exception:
            pass

        # Click "+" on the "Новое" column
        page.click(".o_kanban_header:has-text('Новое') .o_kanban_quick_add")
        page.wait_for_selector(".o_kanban_quick_create", timeout=5000)
        page.wait_for_timeout(500)
        page.screenshot(path=str(SCREENSHOTS_DIR / "qc_02_open.png"))
        print("Screenshot 2: quick create opened")

        form = page.locator(".o_kanban_quick_create")

        # Print all inputs for debugging
        print("Fields in form:")
        for inp in form.locator("input, select").all():
            attrs = {
                "name": inp.get_attribute("name"),
                "id": inp.get_attribute("id"),
                "placeholder": inp.get_attribute("placeholder"),
                "type": inp.get_attribute("type"),
            }
            print(f"  {attrs}")

        # Fill phone (first input with phone-related placeholder or name)
        phone = form.locator("input[placeholder*='Телефон'], input[placeholder*='Phone'], [name='phone'] input").first
        phone.click()
        phone.fill("+7 778 601 0001")
        page.wait_for_timeout(300)

        # Fill contact_name
        name_inp = form.locator("input[placeholder*='Имя'], input[placeholder*='Contact']").first
        name_inp.click()
        name_inp.fill("Тест Пользователь")
        page.wait_for_timeout(300)

        page.screenshot(path=str(SCREENSHOTS_DIR / "qc_03_filled.png"))
        print("Screenshot 3: text fields filled")

        # Fill deal type (Odoo dropdown - click then pick option)
        deal_input = page.locator("#search_deal_type_0")
        deal_input.click()
        page.wait_for_timeout(400)
        page.screenshot(path=str(SCREENSHOTS_DIR / "qc_03b_deal_dropdown.png"))
        # Try to select "Покупка" / "sale" option
        option = page.locator(".o_select_menu_item:has-text('Покупка'), .dropdown-item:has-text('Покупка')")
        if option.count() > 0:
            option.first.click()
            print("Filled deal_type=Покупка")
        else:
            # Try typing
            deal_input.fill("Покупка")
            page.wait_for_timeout(400)
            opt2 = page.locator(".o_select_menu_item, .dropdown-item").first
            if opt2.count() > 0:
                opt2.click()
            print("Filled deal_type via typing")

        # Fill property type
        prop_input = page.locator("#search_property_type_0")
        prop_input.click()
        page.wait_for_timeout(400)
        option2 = page.locator(".o_select_menu_item:has-text('Квартира'), .dropdown-item:has-text('Квартира')")
        if option2.count() > 0:
            option2.first.click()
            print("Filled property_type=Квартира")

        page.screenshot(path=str(SCREENSHOTS_DIR / "qc_04_all_filled.png"))
        print("Screenshot 4: all fields filled")

        # Click "Добавить" (Add)
        add_btn = page.locator(".o_kanban_quick_create button.o_kanban_add")
        print(f"Add button text: '{add_btn.text_content().strip()}'")
        add_btn.click()
        page.wait_for_timeout(2000)

        page.screenshot(path=str(SCREENSHOTS_DIR / "qc_05_after_add.png"))
        print("Screenshot 5: after clicking Add")

        # Check if error dialog opened
        dialog_count = page.locator(".o_dialog, .modal-dialog").count()
        if dialog_count > 0:
            title_el = page.locator(".o_dialog_title, .modal-title")
            title = title_el.text_content() if title_el.count() > 0 else "unknown"
            print(f"\n*** DIALOG OPENED: '{title}' — this means save FAILED ***")
            page.screenshot(path=str(SCREENSHOTS_DIR / "qc_06_dialog.png"))
            print("Screenshot 6: dialog")
        else:
            print("\nNo dialog — save succeeded, card added to kanban")

        print("\n=== NETWORK ERRORS ===")
        if responses:
            for r in responses:
                print(json.dumps(r, indent=2, ensure_ascii=False)[:800])
        else:
            print("No RPC errors captured")

        print("\n=== CONSOLE ERRORS ===")
        if errors:
            for e in errors[:20]:
                print(e)
        else:
            print("No console errors")


if __name__ == "__main__":
    run()
