"""
Unfollower module — unfollows accounts you're following on X.com.

Two modes:
    1. Interactive (default): scan following list → show numbered list → select who to unfollow.
    2. --all: unfollow everyone without scanning.

Strategy:
    1. Navigate to /{username}/following
    2. Either scan to collect account data, or go straight to unfollowing
    3. For each selected account: click "Following" → "Unfollow" confirm
"""

import re
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException


def _parse_selection(selection_str: str, max_index: int) -> set:
    """
    Parse a selection string like "1,3,5-8,all" into a set of 0-based indices.

    Args:
        selection_str: User input string.
        max_index: Maximum valid 1-based index.

    Returns:
        Set of 0-based indices.
    """
    selected = set()
    parts = [p.strip() for p in selection_str.split(",")]

    for part in parts:
        if part.lower() == "all":
            return set(range(max_index))
        if "-" in part:
            try:
                start, end = part.split("-", 1)
                start, end = int(start.strip()), int(end.strip())
                for i in range(start, end + 1):
                    if 1 <= i <= max_index:
                        selected.add(i - 1)
            except ValueError:
                print(f"  [!] Invalid range: '{part}' — skipping.")
        else:
            try:
                i = int(part)
                if 1 <= i <= max_index:
                    selected.add(i - 1)
            except ValueError:
                print(f"  [!] Invalid number: '{part}' — skipping.")
    return selected


def scan_following(driver, limit: int) -> list:
    """
    Scroll through the following list and collect account information.

    Args:
        driver: Authenticated Selenium WebDriver.
        limit: Maximum number of accounts to collect.

    Returns:
        List of dicts: [{index, display_name, handle}, ...]
    """
    print(f"\n[*] Scanning up to {limit} accounts you follow...")
    accounts = []
    seen = set()

    while len(accounts) < limit:
        try:
            cells = driver.find_elements(By.CSS_SELECTOR, "[data-testid='UserCell']")
        except NoSuchElementException:
            cells = []

        for cell in cells:
            if len(accounts) >= limit:
                break
            try:
                # Get the handle from the link
                try:
                    link_el = cell.find_element(By.CSS_SELECTOR, "a[href^='/']")
                    href = link_el.get_attribute("href")
                    handle = href.rstrip("/").split("/")[-1]
                except NoSuchElementException:
                    handle = "unknown"

                if handle in seen:
                    continue
                seen.add(handle)

                # Get display name
                try:
                    name_els = cell.find_elements(By.CSS_SELECTOR, "[data-testid='UserCell'] span")
                    display_name = name_els[0].text if name_els else handle
                except NoSuchElementException:
                    display_name = handle

                accounts.append({
                    "index": len(accounts) + 1,
                    "display_name": display_name,
                    "handle": handle,
                })
                print(f"  [*] Scanned {len(accounts)}/{limit} accounts...", end="\r")

            except Exception:
                continue

        # Scroll
        last_height = driver.execute_script("return document.body.scrollHeight")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(3)
        new_height = driver.execute_script("return document.body.scrollHeight")

        if new_height == last_height:
            print(f"\n[+] Reached bottom of list. Found {len(accounts)} accounts.")
            break

    print(f"\n[+] Scan complete. Collected {len(accounts)} accounts.")
    return accounts


def unfollow_selected(driver, accounts: list, selected_indices: set, wait_time: float = 3.0) -> int:
    """
    Unfollow only the accounts at the given indices.

    Returns count of successfully unfollowed accounts.
    """
    wait = WebDriverWait(driver, 10)
    print(f"\n[*] Processing {len(selected_indices)} selected account(s)...\n")

    unfollowed = 0
    for idx in sorted(selected_indices):
        account = accounts[idx]
        print(f"  [{account['index']}] Unfollowing @{account['handle']} ({account['display_name']})...")

        try:
            buttons = driver.find_elements(By.CSS_SELECTOR, "[data-testid$='-unfollow']")
        except NoSuchElementException:
            buttons = []

        unfollowed_this = False
        for button in buttons:
            try:
                parent_text = button.find_element(By.XPATH, "./ancestor::*[@data-testid='UserCell']").text
                if account["handle"] in parent_text or account["display_name"] in parent_text:
                    driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center'});", button
                    )
                    time.sleep(1)
                    button.click()

                    confirm = wait.until(
                        EC.element_to_be_clickable(
                            (By.CSS_SELECTOR, "[data-testid='confirmationSheetConfirm']")
                        )
                    )
                    confirm.click()

                    unfollowed += 1
                    unfollowed_this = True
                    print(f"    [+] Unfollowed. ({unfollowed}/{len(selected_indices)})")
                    time.sleep(wait_time)
                    break
            except (ElementClickInterceptedException, NoSuchElementException):
                continue
            except Exception:
                continue

        if not unfollowed_this:
            print(f"    [!] Could not locate unfollow button — skipping.")

    return unfollowed


def unfollow_all(driver, wait_time: float = 3.0) -> int:
    """
    Unfollow every account without scanning first.

    This is the --all mode — fast, no preview.
    """
    wait = WebDriverWait(driver, 10)

    print("\n" + "=" * 60)
    print("  UNFOLLOW MODE (--all) — Press Ctrl+C to stop early")
    print("=" * 60 + "\n")

    unfollowed = 0

    while True:
        try:
            buttons = driver.find_elements(
                By.CSS_SELECTOR, "[data-testid$='-unfollow']"
            )
        except NoSuchElementException:
            buttons = []

        if not buttons:
            print("[?] No 'Following' buttons visible. Scrolling...")

        for button in buttons:
            try:
                driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", button
                )
                time.sleep(1)

                button.click()

                confirm = wait.until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, "[data-testid='confirmationSheetConfirm']")
                    )
                )
                confirm.click()

                unfollowed += 1
                print(f"[+] Unfollowed account. Total: {unfollowed}")

                time.sleep(wait_time)

            except ElementClickInterceptedException:
                print("[!] Click intercepted — re-scanning...")
                break
            except Exception:
                print("[!] Element went stale — re-scanning...")
                break

        # Scroll detection
        last_height = driver.execute_script("return document.body.scrollHeight")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(4)
        new_height = driver.execute_script("return document.body.scrollHeight")

        if new_height == last_height:
            print("\n[+] Hit the bottom of the list. Done!")
            break

    return unfollowed


def run(username: str, driver, all_following: bool = False, limit: int = None, wait_time: float = 3.0) -> int:
    """
    Main entry point for unfollowing.

    Args:
        username: X.com handle.
        driver: Authenticated Selenium WebDriver.
        all_following: If True, unfollow everyone without scanning (--all mode).
        limit: Max accounts to scan (None = prompt interactively).
        wait_time: Rate-limiting delay between unfollows.

    Returns:
        Total number of accounts unfollowed.
    """
    print(f"\n[*] Navigating to Following list: https://x.com/{username}/following")
    driver.get(f"https://x.com/{username}/following")
    time.sleep(5)

    # --- --all mode: unfollow everyone immediately ---
    if all_following:
        return unfollow_all(driver, wait_time=wait_time)

    # --- Interactive mode: scan → list → select → unfollow ---
    # Ask for scan limit if not provided via CLI
    if limit is None:
        while True:
            try:
                raw = input("\n  How many accounts do you want to scan? [50]: ").strip()
                limit = int(raw) if raw else 50
                if limit > 0:
                    break
                print("  [!] Enter a positive number.")
            except ValueError:
                print("  [!] Enter a valid number.")
            except (EOFError, KeyboardInterrupt):
                print("\n  [*] Cancelled.")
                return 0

    accounts = scan_following(driver, limit)

    if not accounts:
        print("\n[!] No accounts found to unfollow.")
        return 0

    # Display the list
    print("\n" + "=" * 60)
    print(f"  FOLLOWING ({len(accounts)} total)")
    print("=" * 60)
    for a in accounts:
        print(f"  [{a['index']:>3}] @{a['handle']:<20} {a['display_name']}")

    # Prompt for selection
    print("\n  Enter account numbers to unfollow (e.g., 1,3,5-8 or 'all').")
    print("  Press Enter to cancel.")
    while True:
        try:
            selection = input("  Selection: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  [*] Cancelled.")
            return 0

        if not selection:
            print("  [*] No selection made. Exiting.")
            return 0

        selected = _parse_selection(selection, len(accounts))
        if not selected:
            print("  [!] No valid account numbers parsed. Try again or press Enter to cancel.")
            continue

        print(f"\n  You selected {len(selected)} account(s). Proceed? [Y/n]: ", end="")
        try:
            confirm = input().strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n  [*] Cancelled.")
            return 0

        if confirm in ("", "y", "yes"):
            return unfollow_selected(driver, accounts, selected, wait_time=wait_time)
        else:
            print("  [*] Cancelled.")
            return 0
