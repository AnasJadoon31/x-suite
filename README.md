# 🧰 X Suite

A modular CLI toolkit for X.com (Twitter) account management.  
Easily extendable — add your own commands as new modules.

## ✨ Features

| Command      | Description                        |
|-------------|------------------------------------|
| `delete`    | Undo **all** reposts on your timeline |
| `unfollow`  | Unfollow **everyone** you're following |

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
1. Choose action (delete reposts / unfollow)
2. Enter your X handle (e.g., `anasjadoon31`)
3. Provide the path to your `x-cookies.json`

### Command-line arguments

```bash
# Skip prompts — go straight to repost deletion
python -m xsuite delete -u anasjadoon31 -c ./x-cookies.json

# Unfollow with all arguments
python -m xsuite unfollow -u anasjadoon31 -c ~/Downloads/x-cookies.json

# Run headless (no browser window)
python -m xsuite delete -u anasjadoon31 -c ./x-cookies.json --headless
```

### If installed as a system command

```bash
xsuite                    # interactive
xsuite delete -u johndoe -c ./cookies.json
xsuite unfollow --help
```

## 🧱 Project Structure

```
x-suite/
├── xsuite/
│   ├── __init__.py       # Package info & version
│   ├── __main__.py       # Enables `python -m xsuite`
│   ├── cli.py            # CLI entry point (prompts, argparse)
│   ├── auth.py           # Cookie loading & browser setup
│   ├── deleter.py        # Undo reposts logic
│   └── unfollower.py     # Unfollow logic
├── pyproject.toml        # Modern Python packaging
├── requirements.txt      # Dependencies
└── README.md
```

## ➕ Adding New Features

The tool is **modular by design**. To add a new command (e.g., `likes` to unlike all posts):

1. Create `xsuite/likes.py` with a `run(username, driver) -> int` function.
2. Import it in `xsuite/cli.py`.
3. Add it to the argument parser `choices` and the interactive menu.

That's it!

## ⚠️ Safety Notes

- This tool automates real actions on your X.com account. **Use responsibly.**
- X.com may **rate-limit** or **temporarily lock** accounts that perform too many actions too quickly.  
  The tool includes built-in delays (`wait_time`) to mitigate this.
- Keep your `x-cookies.json` **private** — it grants full access to your session.
- Add `x-cookies.json` to your `.gitignore`!

## 📄 License

MIT © Anas Jadoon
