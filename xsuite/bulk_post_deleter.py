"""
Post Deleter module — deletes personal tweets/posts from your X.com profile.

Two modes:
    1. Interactive (default): scan recent posts → show numbered list → select which to delete.
    2. --all: delete every post without scanning.

Strategy:
    1. Navigate to the user's profile /{username}
    2. Either scan to collect post data, or go straight to deletion
    3. For each selected tweet: click "More" (caret) → "Delete" → confirm
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


def _delete_one_post(driver, article, wait) -> bool:
    """
    Delete a single tweet given its article element.

    Returns True if successful, False otherwise.
    """
    try:
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", article
        )
        time.sleep(1)

        # Click the "More" (caret) button
        caret = article.find_element(By.CSS_SELECTOR, "[data-testid='caret']")
        caret.click()
        time.sleep(1)

        # Find and click the "Delete" menu item
        menuitems = driver.find_elements(
            By.CSS_SELECTOR, "[data-testid='Dropdown'] [role='menuitem']"
        )
        clicked = False
        for item in menuitems:
            if "delete" in item.text.lower():
                item.click()
                clicked = True
                break

        if not clicked:
            driver.execute_script(
                "arguments[0].click();",
                driver.find_element(By.CSS_SELECTOR, "[data-testid='primaryColumn']")
            )
            return False

        time.sleep(1)

        # Confirm deletion
        confirm = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "[data-testid='confirmationSheetConfirm']")
            )
        )
        confirm.click()
        return True

    except (ElementClickInterceptedException, NoSuchElementException):
        return False
    except Exception:
        return False


def scan_posts(driver, limit: int) -> list:
    """
    Scroll through the profile and collect tweet information.

    Args:
        driver: Authenticated Selenium WebDriver.
        limit: Maximum number of posts to collect.

    Returns:
        List of dicts: [{index, text_preview, date, permalink}, ...]
    """
    print(f"\n[*] Scanning up to {limit} recent posts...")
    posts = []
    seen = set()

    while len(posts) < limit:
        try:
            articles = driver.find_elements(By.CSS_SELECTOR, "[data-testid='tweet']")
        except NoSuchElementException:
            articles = []

        for article in articles:
            if len(posts) >= limit:
                break
            try:
                # Unique identifier via permalink
                try:
                    link_el = article.find_element(By.CSS_SELECTOR, "a[href*='/status/']")
                    permalink = link_el.get_attribute("href")
                except NoSuchElementException:
                    permalink = article.get_attribute("aria-labelledby") or str(article.location)

                if permalink in seen:
                    continue
                seen.add(permalink)

                # Text preview
                try:
                    text_el = article.find_element(By.CSS_SELECTOR, "[data-testid='tweetText']")
                    text = text_el.text.replace("\n", " ")[:80]
                except NoSuchElementException:
                    text = "(no text)"

                # Date
                try:
                    time_el = article.find_element(By.CSS_SELECTOR, "time")
                    date = time_el.get_attribute("datetime") or time_el.text or "?"
                except NoSuchElementException:
                    date = "?"

                posts.append({
                    "index": len(posts) + 1,
                    "text_preview": text,
                    "date": date,
                    "permalink": permalink,
                })
                print(f"  [*] Scanned {len(posts)}/{limit} posts...", end="\r")

            except Exception:
                continue

        # Scroll
        last_height = driver.execute_script("return document.body.scrollHeight")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(3)
        new_height = driver.execute_script("return document.body.scrollHeight")

        if new_height == last_height:
            print(f"\n[+] Reached bottom of timeline. Found {len(posts)} posts.")
            break

    print(f"\n[+] Scan complete. Collected {len(posts)} posts.")
    return posts


def delete_selected_posts(driver, posts: list, selected_indices: set, wait_time: float = 3.0) -> int:
    """
    Delete only the posts at the given indices.

    Returns count of successfully deleted posts.
    """
    wait = WebDriverWait(driver, 10)
    print(f"\n[*] Deleting {len(selected_indices)} selected post(s)...\n")

    deleted = 0
    for idx in sorted(selected_indices):
        post = posts[idx]
        print(f"  [{post['index']}] Deleting: {post['text_preview'][:60]}...")

        # Re-find the tweet element by permalink
        try:
            status_id = post['permalink'].split('/status/')[-1].split('?')[0].split('#')[0]
            link_el = driver.find_element(By.CSS_SELECTOR, f"a[href*='{status_id}']")
            article = link_el.find_element(By.XPATH, "./ancestor::*[@data-testid='tweet']")
        except NoSuchElementException:
            try:
                articles = driver.find_elements(By.CSS_SELECTOR, "[data-testid='tweet']")
                article = articles[idx % len(articles)] if articles else None
            except Exception:
                article = None

        if article is None:
            print(f"    [!] Could not locate tweet — skipping.")
            continue

        if _delete_one_post(driver, article, wait):
            deleted += 1
            print(f"    [+] Deleted. ({deleted}/{len(selected_indices)})")
        else:
            print(f"    [!] Failed to delete — skipping.")

        time.sleep(wait_time)

    return deleted


def delete_all_posts(driver, wait_time: float = 3.0) -> int:
    """
    Delete every post on the profile without scanning first.

    This is the --all mode — fast, no preview.
    """
    wait = WebDriverWait(driver, 10)

    print("\n" + "=" * 60)
    print("  TWEET DELETER MODE (--all) — Press Ctrl+C to stop early")
    print("=" * 60 + "\n")

    deleted = 0
    seen = set()

    while True:
        try:
            articles = driver.find_elements(By.CSS_SELECTOR, "[data-testid='tweet']")
        except NoSuchElementException:
            articles = []

        if not articles:
            print("[?] No tweets visible. Scrolling...")

        for article in articles:
            try:
                tweet_id = article.get_attribute("aria-labelledby") or str(article.location)
                if tweet_id in seen:
                    continue
                seen.add(tweet_id)

                if _delete_one_post(driver, article, wait):
                    deleted += 1
                    print(f"[+] Deleted a tweet. Total: {deleted}")
                time.sleep(wait_time)

            except Exception:
                print("[!] Element went stale — re-scanning...")
                break

        # Scroll detection
        last_height = driver.execute_script("return document.body.scrollHeight")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(4)
        new_height = driver.execute_script("return document.body.scrollHeight")

        if new_height == last_height:
            print("\n[+] Hit the bottom of the timeline. Done!")
            break

    return deleted


def run(username: str, driver, all_posts: bool = False, limit: int = None, wait_time: float = 3.0) -> int:
    """
    Main entry point for post deletion.

    Args:
        username: X.com handle.
        driver: Authenticated Selenium WebDriver.
        all_posts: If True, delete everything without scanning (--all mode).
        limit: Max posts to scan (None = prompt interactively).
        wait_time: Rate-limiting delay between deletions.

    Returns:
        Total number of tweets deleted.
    """
    print(f"\n[*] Navigating to profile: https://x.com/{username}")
    driver.get(f"https://x.com/{username}")
    time.sleep(5)

    # --- --all mode: delete everything immediately ---
    if all_posts:
        return delete_all_posts(driver, wait_time=wait_time)

    # --- Interactive mode: scan → list → select → delete ---
    # Ask for scan limit if not provided via CLI
    if limit is None:
        while True:
            try:
                raw = input("\n  How many recent posts do you want to scan? [50]: ").strip()
                limit = int(raw) if raw else 50
                if limit > 0:
                    break
                print("  [!] Enter a positive number.")
            except ValueError:
                print("  [!] Enter a valid number.")
            except (EOFError, KeyboardInterrupt):
                print("\n  [*] Cancelled.")
                return 0

    posts = scan_posts(driver, limit)

    if not posts:
        print("\n[!] No posts found to delete.")
        return 0

    # Display the list
    print("\n" + "=" * 60)
    print(f"  SCANNED POSTS ({len(posts)} total)")
    print("=" * 60)
    for p in posts:
        print(f"  [{p['index']:>3}] {p['date'][:10] if p['date'] else '?'}  {p['text_preview']}")

    # Prompt for selection
    print("\n  Enter post numbers to delete (e.g., 1,3,5-8 or 'all').")
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

        selected = _parse_selection(selection, len(posts))
        if not selected:
            print("  [!] No valid post numbers parsed. Try again or press Enter to cancel.")
            continue

        print(f"\n  You selected {len(selected)} post(s). Proceed? [Y/n]: ", end="")
        try:
            confirm = input().strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n  [*] Cancelled.")
            return 0

        if confirm in ("", "y", "yes"):
            return delete_selected_posts(driver, posts, selected, wait_time=wait_time)
        else:
            print("  [*] Cancelled.")
            return 0
