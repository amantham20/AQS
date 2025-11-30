# AQS — Agile Quick Search

A fast CLI tool to fuzzy-search your shell command history using `fzf`. Find and re-run recent commands instantly.

## Features

- 🔍 Fuzzy search through bash, zsh, and fish history
- ⚡ Smart sorting prioritizes exact and prefix matches
- 🚀 Opens interactive fzf picker
- ▶️ Executes selected command automatically (or use `-d` for dry-run)
- 📦 Single binary, no dependencies at runtime (except `fzf`)

## Installation

### Prerequisites

You need `fzf` installed:

```bash
# macOS
brew install fzf

# Ubuntu/Debian
sudo apt install fzf

# Arch
sudo pacman -S fzf
```

### Download Binary

Download the latest release for your platform from the [Releases](https://github.com/amantham20/aqs/releases) page.

```bash
# macOS (Apple Silicon)
curl -L https://github.com/amantham20/aqs/releases/latest/download/aqs-macos-arm64 -o aqs
chmod +x aqs
sudo mv aqs /usr/local/bin/

# macOS (Intel)
curl -L https://github.com/amantham20/aqs/releases/latest/download/aqs-macos-amd64 -o aqs
chmod +x aqs
sudo mv aqs /usr/local/bin/

# Linux
curl -L https://github.com/amantham20/aqs/releases/latest/download/aqs-linux-amd64 -o aqs
chmod +x aqs
sudo mv aqs /usr/local/bin/

# Windows (PowerShell)
Invoke-WebRequest -Uri https://github.com/amantham20/aqs/releases/latest/download/aqs-windows-amd64.exe -OutFile aqs.exe
```

### Install via pip

```bash
pip install git+https://github.com/amantham20/aqs.git
```

### Install from source

```bash
git clone https://github.com/amantham20/aqs.git
cd aqs
pip install -e .
```

## Usage

```bash
# Open fzf with all history, execute selected command
aqs

# Pre-filter with a query (e.g., find git commands)
aqs git

# Dry-run: print selected command without executing
aqs -d
aqs git -d
```

## Options

```
Usage: aqs [OPTIONS] [QUERY]

  AQS — fuzzy search recent commands.

Options:
  -d, --dry-run  Dry run: print selected command without executing
  --help         Show this message and exit.
```

## How It Works

1. Reads history from `~/.bash_history`, `~/.zsh_history`, and fish history
2. Deduplicates commands (keeping most recent occurrence)
3. If a query is provided, pre-sorts by similarity (exact > prefix > substring > fuzzy)
4. Opens `fzf` for interactive selection
5. Executes the selected command (unless `-d` flag is used)

## Shell Integration

Add an alias or keybinding for quick access:

### Bash/Zsh
```bash
# Add to ~/.bashrc or ~/.zshrc
alias h='aqs'
```

### Fish
```fish
# Add to ~/.config/fish/config.fish
alias h='aqs'
```

## License

MIT
