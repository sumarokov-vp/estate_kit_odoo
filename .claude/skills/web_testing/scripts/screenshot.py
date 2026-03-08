"""Take a screenshot of an Odoo page.

Usage: uv run screenshot.py <path_or_url> [filename.png]
"""

import sys
from common import BrowserSession, SCREENSHOTS_DIR

path_or_url = sys.argv[1]
output = sys.argv[2] if len(sys.argv) > 2 else "screenshot.png"

with BrowserSession() as s:
    s.goto(path_or_url)
    path = SCREENSHOTS_DIR / output
    s.page.screenshot(path=str(path), full_page=True)
    print(f"Screenshot: {path}")
    print(f"URL: {s.page.url}")
    print(f"Title: {s.page.title()}")
