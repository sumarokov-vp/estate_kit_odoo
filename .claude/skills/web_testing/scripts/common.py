"""Common browser utilities for Odoo web testing."""

import json
import os
import sys
from pathlib import Path

import yaml
from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

PROJECT_ROOT = Path(__file__).resolve().parents[4]
CONFIG_FILE = PROJECT_ROOT / ".claude" / "devops.yaml"
DATA_DIR = Path("/tmp/claude-browser/odoo")
SCREENSHOTS_DIR = DATA_DIR / "screenshots"

DATA_DIR.mkdir(parents=True, exist_ok=True)
SCREENSHOTS_DIR.mkdir(exist_ok=True)

# Environment: dev (default) or prod
ENV = os.environ.get("ODOO_ENV", "dev")


def _load_config():
    with open(CONFIG_FILE) as f:
        config = yaml.safe_load(f)
    wt = config.get("web_testing", {})

    if ENV in wt and isinstance(wt[ENV], dict):
        env_config = wt[ENV]
    else:
        env_config = wt

    url = env_config.get("url", "")
    # Credentials from env vars (set via: set -x ODOO_EMAIL (pass ... | grep ...))
    email = os.environ.get("ODOO_EMAIL", "")
    password = os.environ.get("ODOO_PASSWORD", "")

    return url, email, password


BASE_URL, AUTH_EMAIL, AUTH_PASSWORD = _load_config()
COOKIES_FILE = DATA_DIR / f".cookies-{ENV}.json"


def _load_cookies(context: BrowserContext) -> bool:
    if COOKIES_FILE.exists():
        cookies = json.loads(COOKIES_FILE.read_text())
        if cookies:
            context.add_cookies(cookies)
            return True
    return False


def _save_cookies(context: BrowserContext) -> None:
    COOKIES_FILE.write_text(json.dumps(context.cookies(), indent=2))


def _extract_base_url(url: str) -> str:
    """Extract base URL (scheme + host + port) from a full URL."""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    return base


def _auto_login(page: Page, target_url: str = "") -> None:
    """Login to Odoo. Uses base URL from target_url if provided, else BASE_URL."""
    login_base = _extract_base_url(target_url) if target_url else BASE_URL
    page.goto(f"{login_base}/web/login", wait_until="load")
    page.wait_for_timeout(2000)

    if "/web/login" not in page.url:
        return

    page.fill('input[name="login"]', AUTH_EMAIL)
    page.fill('input[name="password"]', AUTH_PASSWORD)
    page.click('button[type="submit"]')
    page.wait_for_load_state("load")
    page.wait_for_timeout(3000)

    if "/web/login" in page.url:
        print(f"ERROR: Login failed on {login_base}. Check web_testing.{ENV} in .claude/devops.yaml", file=sys.stderr)
        sys.exit(1)

    _save_cookies(page.context)
    print(f"Logged in as {AUTH_EMAIL} on {login_base}", file=sys.stderr)


def resolve_url(path_or_url: str) -> str:
    if path_or_url.startswith("http"):
        return path_or_url
    return f"{BASE_URL}{path_or_url}"


class BrowserSession:
    def __init__(self) -> None:
        self._pw = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self.page: Page | None = None

    def __enter__(self) -> "BrowserSession":
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=True)
        self._context = self._browser.new_context(viewport={"width": 1920, "height": 1080})
        _load_cookies(self._context)
        self.page = self._context.new_page()
        return self

    def __exit__(self, *args) -> None:
        if self._context:
            _save_cookies(self._context)
        if self._browser:
            self._browser.close()
        if self._pw:
            self._pw.stop()

    def goto(self, path_or_url: str, wait_ms: int = 3000) -> None:
        url = resolve_url(path_or_url)
        self.page.goto(url, wait_until="load")
        self.page.wait_for_timeout(1000)

        if "/web/login" in self.page.url:
            _auto_login(self.page, target_url=url)
            self.page.goto(url, wait_until="load")
            self.page.wait_for_timeout(wait_ms)
        else:
            self.page.wait_for_timeout(wait_ms - 1000)
