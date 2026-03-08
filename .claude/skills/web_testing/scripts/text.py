"""Get text content of an element on an Odoo page.

Usage: uv run text.py <path_or_url> <selector>
"""

import sys
from common import BrowserSession

path_or_url = sys.argv[1]
selector = sys.argv[2]

with BrowserSession() as s:
    s.goto(path_or_url)
    element = s.page.query_selector(selector)
    if element:
        print(element.inner_text())
    else:
        print(f"Element not found: {selector}", file=sys.stderr)
        sys.exit(1)
