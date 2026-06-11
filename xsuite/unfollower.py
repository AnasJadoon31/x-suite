"""
Unfollower module — unfollows everyone you're currently following on X.com.

Strategy:
    1. Navigate to /{username}/following
    2. Repeatedly find & click "Following" → "Unfollow" confirm
    3. Scroll until the bottom of the list is reached
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException


def run(username: str, driver, wait_time: float = 3.0) -> int:
    """
    Execute the unfollow sequence.

    Args:
        username: The X.com handle to operate on.
        driver: An authenticated Selenium WebDriver.
        wait_time: Seconds to sleep between unfollows (rate-limiting).

    Returns:
        Total number of accounts unfollowed.
    """
    wait = WebDriverWait(driver, 10)
    print(f"\n[*] Navigating to Following list: https://x.com/{username}/following")
    driver.get(f"https://x.com/{username}/following")
    time.sleep(5)

    print("\n" + "=" * 60)
    print("  UNFOLLOW MODE — Press Ctrl+C to stop early")
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
