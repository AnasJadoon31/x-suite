"""
CLI module — interactive command-line interface for x-suite.

Usage:
    python -m xsuite            # interactive mode
    python -m xsuite delete     # skip prompt, go straight to repost deletion
    python -m xsuite unfollow   # skip prompt, go straight to unfollow
"""

import sys
import time
import argparse

from . import __version__
from .auth import login
from .deleter import run as run_deleter
from .unfollower import run as run_unfollower


BANNER = r"""
 ▄▄▄  ▄▄▄    ▄▄▄▄                 ██                        
  ██▄▄██   ▄█▀▀▀▀█                ▀▀       ██               
   ████    ██▄       ██    ██   ████     ███████    ▄████▄  
    ██      ▀████▄   ██    ██     ██       ██      ██▄▄▄▄██ 
   ████         ▀██  ██    ██     ██       ██      ██▀▀▀▀▀▀ 
  ██  ██   █▄▄▄▄▄█▀  ██▄▄▄███  ▄▄▄██▄▄▄    ██▄▄▄   ▀██▄▄▄▄█ 
 ▀▀▀  ▀▀▀   ▀▀▀▀▀     ▀▀▀▀ ▀▀  ▀▀▀▀▀▀▀▀     ▀▀▀▀     ▀▀▀▀▀
  X Suite — X.com account toolkit
  v{version}
"""


def _prompt_username() -> str:
    """Ask for the X handle interactively."""
    while True:
        username = input("  X handle (without @): ").strip().replace("@", "")
        if username:
            return username
        print("  [!] Please enter a valid handle.")


def _prompt_cookie_path() -> str:
    """Ask for the path to x-cookies.json interactively."""
    while True:
        path = input("  Path to x-cookies.json: ").strip()
        if path:
            return path
        print("  [!] Please enter a valid file path.")


def _prompt_action() -> str:
    """Ask which action the user wants to perform."""
    print("\n  Available actions:")
    print("    [1] Undo all reposts (delete)")
    print("    [2] Unfollow everyone")
    print("    [q] Quit")
    while True:
        choice = input("\n  Choose an option [1/2/q]: ").strip().lower()
        if choice in ("1", "delete"):
            return "delete"
        if choice in ("2", "unfollow"):
            return "unfollow"
        if choice in ("q", "quit", "exit"):
            return "quit"
        print("  [!] Invalid choice. Enter 1, 2, or q.")


def main():
    parser = argparse.ArgumentParser(
        prog="xsuite",
        description="X Suite — modular X.com account management toolkit.",
    )
    parser.add_argument(
        "action",
        nargs="?",
        choices=["delete", "unfollow"],
        help="Action to perform (if omitted, runs in interactive mode).",
    )
    parser.add_argument(
        "--username", "-u",
        help="X handle to operate on (skips prompt).",
    )
    parser.add_argument(
        "--cookies", "-c",
        help="Path to x-cookies.json (skips prompt).",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run Chrome in headless mode (no GUI).",
    )
    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"x-suite v{__version__}",
    )

    args = parser.parse_args()

    print(BANNER.format(version=__version__))

    # --- Resolve action ---
    action = args.action
    if action is None:
        action = _prompt_action()

    if action == "quit":
        print("\n  Goodbye!")
        sys.exit(0)

    # --- Resolve username ---
    username = args.username
    if username is None:
        username = _prompt_username()

    # --- Resolve cookie path ---
    cookie_path = args.cookies
    if cookie_path is None:
        cookie_path = _prompt_cookie_path()

    # --- Authenticate ---
    print()
    driver = login(username, cookie_path, headless=args.headless)

    try:
        count: int = 0
        if action == "delete":
            count = run_deleter(username, driver)
            label = "reposts undone"
        elif action == "unfollow":
            count = run_unfollower(username, driver)
            label = "accounts unfollowed"

        print(f"\n[+] Done! Total {label}: {count}")

    except KeyboardInterrupt:
        print("\n\n[!] Interrupted by user. Shutting down gracefully...")
    except Exception as e:
        print(f"\n[!] FATAL ERROR: {e}")
    finally:
        print("[*] Shutting down WebDriver...")
        driver.quit()
        print("[*] Goodbye!")
