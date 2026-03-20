"""Click an element on an Odoo page and take a screenshot.

Usage: uv run click.py <path_or_url> <selector> [filename.png]
"""

import sys

from common import SCREENSHOTS_DIR, BrowserSession

path_or_url = sys.argv[1]
selector = sys.argv[2]
output = sys.argv[3] if len(sys.argv) > 3 else "click_result.png"

with BrowserSession() as s:
    s.goto(path_or_url)
    s.page.click(selector)
    s.page.wait_for_timeout(3000)
    path = SCREENSHOTS_DIR / output
    s.page.screenshot(path=str(path), full_page=True)
    print(f"Clicked: {selector}")
    print(f"Screenshot: {path}")
    print(f"URL: {s.page.url}")
