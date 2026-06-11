"""
Authentication module — loads X.com session cookies and initialises
a Selenium WebDriver with the authenticated session.

Works cross-platform (Windows, macOS, Linux).
"""

import json
import sys
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


def resolve_cookie_path(raw_path: str) -> Path:
    """Resolve and validate the cookie file path.

    Tries, in order:
        1. The path exactly as given (supports absolute & CWD-relative).
        2. Relative to the user's home directory (~).
    """
    candidates = [
        Path(raw_path).expanduser().resolve(),          # exact path + ~ expansion
        Path.home() / raw_path,                          # relative to home
    ]

    for path in candidates:
        path = path.resolve()
        if path.exists():
            if path.suffix != ".json":
                print(f"[!] WARNING: Cookie file does not have a .json extension — trying anyway...")
            return path

    # None found — report the first candidate as the most likely expected location
    print(f"[!] ERROR: Cookie file not found.")
    print(f"     Tried: {candidates[0]}")
    print(f"     Tried: {candidates[1]}")
    print("     Export your cookies using 'Cookie-Editor' while logged into x.com.")
    sys.exit(1)


def load_cookies(filepath: Path) -> list[dict]:
    """Load cookies from a JSON file exported by Cookie-Editor."""
    print(f"[*] Loading cookies from: {filepath}")
    try:
        with open(filepath, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print("[!] ERROR: Cookie file is not valid JSON.")
        sys.exit(1)
    return data


def build_chrome_options(headless: bool = False) -> Options:
    """Build Chrome options with anti-bot-detection flags."""
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    # Common flags to reduce detection and improve stability across OSes
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    return options


def create_driver(headless: bool = False) -> webdriver.Chrome:
    """Create and return a Chrome WebDriver with auto-downloaded driver binary."""
    print("[*] Initialising Chrome WebDriver (this may take a moment on first run)...")
    options = build_chrome_options(headless)
    # webdriver_manager handles OS detection automatically
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def inject_session(driver: webdriver.Chrome, cookies: list[dict]) -> None:
    """Navigate to x.com, inject cookies, and refresh to authenticate."""
    print("[*] Navigating to x.com and injecting session cookies...")
    driver.get("https://x.com")

    for cookie in cookies:
        cookie_dict = {
            "name": cookie["name"],
            "value": cookie["value"],
            "domain": ".x.com",
            "secure": cookie.get("secure", True),
        }
        # Handle optional fields that may cause errors
        for key in ("path", "expiry", "sameSite"):
            if key in cookie:
                cookie_dict[key] = cookie[key]
        try:
            driver.add_cookie(cookie_dict)
        except Exception:
            pass  # Some cookies may be rejected; this is harmless

    driver.refresh()
    time.sleep(3)


def login(username: str, cookie_path: str, headless: bool = False) -> webdriver.Chrome:
    """
    Full authentication flow:
        1. Resolve & load cookies
        2. Start Chrome
        3. Inject session
    Returns an authenticated WebDriver instance.
    """
    path = resolve_cookie_path(cookie_path)
    cookies = load_cookies(path)
    driver = create_driver(headless)
    inject_session(driver, cookies)
    return driver
