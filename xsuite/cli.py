"""
CLI module — interactive command-line interface for x-suite.

Usage:
    python -m xsuite              # interactive mode
    python -m xsuite delete       # skip prompt, go straight to repost deletion
    python -m xsuite unfollow     # skip prompt, go straight to unfollow (interactive select)
    python -m xsuite unfollow --all  # unfollow everyone without scanning
    python -m xsuite clean        # skip prompt, go straight to tweet deletion (interactive select)
    python -m xsuite clean --all     # delete all tweets without scanning
"""

import sys
import time
import argparse

from . import __version__
from .auth import login
from .bulk_repost_deleter import run as run_deleter
from .bulk_unfollower import run as run_unfollower
from .bulk_post_deleter import run as run_cleaner


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
    print("    [2] Unfollow accounts — scan & select, or --all to unfollow everyone")
    print("    [3] Delete tweets — scan & select, or --all to wipe everything")
    print("    [q] Quit")
    while True:
        choice = input("\n  Choose an option [1/2/3/q]: ").strip().lower()
        if choice in ("1", "delete"):
            return "delete"
        if choice in ("2", "unfollow"):
            return "unfollow"
        if choice in ("3", "clean"):
            return "clean"
        if choice in ("q", "quit", "exit"):
            return "quit"
        print("  [!] Invalid choice. Enter 1, 2, 3, or q.")


def _prompt_mode(action_name: str) -> bool:
    """Ask whether to scan & select or blast everything.

    Returns True for 'all' mode, False for scan & select.
    """
    print(f"\n  How do you want to {action_name}?")
    print("    [1] Scan & select — preview before deleting/unfollowing")
    print("    [2] Blast everything — no preview, just do it all")
    print("    [q] Cancel")
    while True:
        choice = input("\n  Choose an option [1/2/q]: ").strip().lower()
        if choice in ("1", "scan", "select"):
            return False
        if choice in ("2", "all", "blast", "everything"):
            return True
        if choice in ("q", "quit", "cancel"):
            return None
        print("  [!] Invalid choice. Enter 1, 2, or q.")


def main():
    parser = argparse.ArgumentParser(
        prog="xsuite",
        description="X Suite — modular X.com account management toolkit.",
    )
    parser.add_argument(
        "action",
        nargs="?",
        choices=["delete", "unfollow", "clean"],
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
        "--all",
        action="store_true",
        dest="all_items",
        help="Delete/unfollow EVERYTHING without scanning or selecting (skip interactive list).",
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=None,
        help="Number of recent items to scan before showing the selection list (default: prompted interactively).",
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
    from_cli = action is not None  # was the action passed on the command line?
    if action is None:
        action = _prompt_action()

    if action == "quit":
        print("\n  Goodbye!")
        sys.exit(0)

    # --- Interactive mode: ask scan vs blast if no --all was given ---
    if not from_cli and action in ("unfollow", "clean") and not args.all_items:
        result = _prompt_mode("unfollow everyone" if action == "unfollow" else "delete all tweets")
        if result is None:
            print("\n  [*] Cancelled.")
            sys.exit(0)
        args.all_items = result

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
            count = run_unfollower(username, driver, all_following=args.all_items, limit=args.limit)
            label = "accounts unfollowed"
        elif action == "clean":
            count = run_cleaner(username, driver, all_posts=args.all_items, limit=args.limit)
            label = "tweets deleted"

        print(f"\n[+] Done! Total {label}: {count}")

    except KeyboardInterrupt:
        print("\n\n[!] Interrupted by user. Shutting down gracefully...")
    except Exception as e:
        print(f"\n[!] FATAL ERROR: {e}")
    finally:
        print("[*] Shutting down WebDriver...")
        driver.quit()
        print("[*] Goodbye!")
