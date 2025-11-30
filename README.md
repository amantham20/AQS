# AQS — Agile Quick Search (cli)

AQS is a tiny CLI tool to fuzzy-search your recent shell command history (bash, zsh, fish). It tries to behave like `fzf` for quickly finding recent commands. If the `fzf` binary is present it uses it for the interactive picker; otherwise it falls back to a simple fuzzy-score-based search using Python.

Features
- Reads from common shell histories (`.bash_history`, `.zsh_history`, fish history).
- Shows recent commands first (deduplicated to prefer most recent occurrences).
- Uses `fzf` when available for an interactive selection; otherwise uses `rapidfuzz` to score and list matches.
- Prints the chosen command so you can `eval $(aqs)` or copy it to clipboard.

Installation (quick)

1. Create a virtualenv and install deps:

```fish
python -m venv .venv
source .venv/bin/activate.fish
pip install -r requirements.txt
```

2. Make the script executable and put it on your PATH (optional):

```fish
chmod +x aqs
mv aqs /usr/local/bin/aqs
```

Usage

Basic interactive (uses `fzf` if installed):

```bash
aqs
# select a command; it will be printed to stdout
# run it in your shell with: eval "$(aqs)"
```

Search without `fzf` (fallback):

```bash
aqs -q git
# prints top fuzzy matches for 'git'
```

Options
- `-s, --shell` : prefer a specific shell history (`bash`, `zsh`, `fish`).
- `-n, --num` : number of history lines to consider (default: 1000).
- `-q, --query` : non-interactive query to list results.
- `-c, --copy` : copy selected/printed command to clipboard (macOS `pbcopy`).

Notes
- The script prints the selected command to stdout. It cannot directly run it in your current shell; use `eval "$(aqs)"` or paste it.

Contributing / Next steps
- Add live interactive fallback with `prompt_toolkit`.
- Add shell integration helpers in `shell/` directory (aliases/functions).

License: MIT style (use as you like)
