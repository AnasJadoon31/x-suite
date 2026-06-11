"""
Deleter module — undoes all reposts on your X.com timeline.

Strategy:
    1. Navigate to the user's profile /{username}
    2. Repeatedly find & click "Undo Repost" → confirm
    3. Scroll until the bottom of the timeline is reached
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


def run(username: str, driver, wait_time: float = 2.0) -> int:
    """
    Execute the repost-deletion sequence.

    Args:
        username: The X.com handle to operate on.
        driver: An authenticated Selenium WebDriver.
        wait_time: Seconds to sleep between deletions (rate-limiting).

    Returns:
        Total number of reposts undone.
    """
    wait = WebDriverWait(driver, 10)
    print(f"\n[*] Navigating to timeline: https://x.com/{username}")
    driver.get(f"https://x.com/{username}")
    time.sleep(5)

    print("\n" + "=" * 60)
    print("  REPOST DELETER MODE — Press Ctrl+C to stop early")
    print("=" * 60 + "\n")

    undone = 0

    while True:
        try:
            buttons = driver.find_elements(
                By.CSS_SELECTOR, "[data-testid='unretweet']"
            )
        except NoSuchElementException:
            buttons = []

        if not buttons:
            print("[?] No repost buttons visible. Scrolling...")

        for button in buttons:
            try:
                driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", button
                )
                time.sleep(1)

                button.click()

                confirm = wait.until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, "[data-testid='unretweetConfirm']")
                    )
                )
                confirm.click()

                undone += 1
                print(f"[+] Undid a repost. Total: {undone}")

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

    return undone
