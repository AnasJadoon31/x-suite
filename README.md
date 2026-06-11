# 🧰 X Suite

A modular CLI toolkit for X.com (Twitter) account management.  
Easily extendable — add your own commands as new modules.

## ✨ Features

| Command      | Description                                                        |
|-------------|--------------------------------------------------------------------|
| `delete`    | Undo **all** reposts on your timeline                               |
| `unfollow`  | Scan & select accounts to unfollow, or `--all` to unfollow everyone |
| `clean`     | Scan & select posts to delete, or `--all` to wipe everything        |

### Interactive Mode (default)
Running `unfollow` or `clean` without `--all` will:
1. Ask how many recent items to scan
2. Scroll your profile/following list and collect previews
3. Display a **numbered list** so you can see what's there
4. Let you pick which ones to delete/unfollow (e.g., `1,3,5-8` or `all`)

## 📦 Installation

```bash
# Clone the repo
git clone https://github.com/AnasJadoon31/x-suite.git
cd x-suite

# Install dependencies
pip install -r requirements.txt

# (Optional) Install as a system-wide CLI tool
pip install .
```

After installing with `pip install .`, you can run `xsuite` from anywhere.

## 🔑 Prerequisites

1. **Google Chrome** installed on your system.
2. A **cookies.json** file exported from your logged-in X.com session:
   - Install the [Cookie-Editor](https://cookie-editor.com/) browser extension.
   - Log into [x.com](https://x.com) in Chrome.
   - Open Cookie-Editor → Export → Copy the JSON.
   - Save it as `x-cookies.json` anywhere on your machine.

## 🚀 Usage

### Interactive mode (recommended)

```bash
python -m xsuite
```

You'll be guided through:
1. Choose action (delete reposts / unfollow / clean tweets)
2. Enter your X handle (e.g., `anasjadoon31`)
3. Provide the path to your `x-cookies.json`
4. For **unfollow** and **clean**: choose how many items to scan, then pick from the list

### Command-line arguments

```bash
# Skip prompts — go straight to repost deletion
python -m xsuite delete -u anasjadoon31 -c ./x-cookies.json

# Unfollow: scan 100 accounts, then select interactively
python -m xsuite unfollow -u anasjadoon31 -c ./x-cookies.json -l 100

# Unfollow EVERYONE immediately (no scan, no preview)
python -m xsuite unfollow -u anasjadoon31 -c ./x-cookies.json --all

# Clean: delete every tweet without scanning
python -m xsuite clean -u anasjadoon31 -c ./x-cookies.json --all

# Clean: scan 30 recent posts and pick which to delete
python -m xsuite clean -u anasjadoon31 -c ./x-cookies.json -l 30

# Run headless (no browser window)
python -m xsuite clean -u anasjadoon31 -c ./x-cookies.json --headless --all
```

### Selection format
When the numbered list appears, enter your choices like:
- `1,3,5` — delete/unfollow items #1, #3, and #5
- `5-10` — delete/unfollow items #5 through #10
- `1,3,5-8,12` — mix of individual and ranges
- `all` — select everything in the scanned list

### If installed as a system command

```bash
xsuite                                    # interactive
xsuite delete -u johndoe -c ./cookies.json
xsuite unfollow -u johndoe -c ./cookies.json --all
xsuite clean --help
```

## 🧱 Project Structure

```
x-suite/
├── xsuite/
│   ├── __init__.py              # Package info & version
│   ├── __main__.py              # Enables `python -m xsuite`
│   ├── cli.py                   # CLI entry point (prompts, argparse)
│   ├── auth.py                  # Cookie loading & browser setup
│   ├── bulk-repost-deleter.py   # Undo reposts logic
│   ├── bulk-unfollower.py       # Unfollow logic (scan-select + --all)
│   └── bulk-post-deleter.py     # Tweet deletion logic (scan-select + --all)
├── pyproject.toml               # Modern Python packaging
├── requirements.txt             # Dependencies
└── README.md
```

## ➕ Adding New Features

The tool is **modular by design**. To add a new command (e.g., `likes` to unlike all posts):

1. Create `xsuite/likes.py` with a `run(username, driver, **kwargs) -> int` function.
2. Import it in `xsuite/cli.py`.
3. Add it to the argument parser `choices` and the interactive menu.

That's it!

## ⚠️ Safety Notes

- This tool automates real actions on your X.com account. **Use responsibly.**
- The `--all` flag deletes/unfollows **everything** without asking for confirmation beyond the initial prompt. Make sure you know what you're doing.
- X.com may rate-limit or temporarily restrict accounts that perform too many actions too quickly. The tool includes built-in delays to reduce this risk.

- X.com may **rate-limit** or **temporarily lock** accounts that perform too many actions too quickly.  
  The tool includes built-in delays (`wait_time`) to mitigate this.
- Keep your `x-cookies.json` **private** — it grants full access to your session.
- Add `x-cookies.json` to your `.gitignore`!

## 📄 License

MIT © Muhammad Anas
