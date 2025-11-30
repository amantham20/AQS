#!/usr/bin/env python3
"""AQS - fuzzy search recent shell commands

Usage: `aqs [options]`
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

import click
from rapidfuzz import process, fuzz


def detect_history_paths(prefer_shell=None):
    home = Path.home()
    paths = []
    if prefer_shell is None or prefer_shell == 'bash':
        paths.append(home / '.bash_history')
    if prefer_shell is None or prefer_shell == 'zsh':
        paths.append(home / '.zsh_history')
    if prefer_shell is None or prefer_shell == 'fish':
        # fish stores history in a YAML-like file
        paths.append(home / '.local' / 'share' / 'fish' / 'fish_history')
    return paths


def read_history(paths, max_lines=1000):
    cmds = []
    for p in paths:
        p = Path(p)
        if not p.exists():
            continue
        try:
            text = p.read_text(errors='ignore')
        except Exception:
            continue
        if 'fish_history' in str(p):
            # fish history: lines like "- cmd: git status"
            for line in text.splitlines():
                line = line.strip()
                if line.startswith('- cmd:'):
                    cmd = line.split(':', 1)[1].strip()
                    if cmd:
                        cmds.append(cmd)
        else:
            for line in text.splitlines():
                line = line.rstrip('\n')
                if not line:
                    continue
                cmds.append(line)
    # history files are usually oldest-first; keep recency by taking tail
    if len(cmds) > max_lines:
        cmds = cmds[-max_lines:]

    # dedupe preserving most recent — iterate reversed and keep first occurrences
    seen = set()
    uniq = []
    for cmd in reversed(cmds):
        if cmd in seen:
            continue
        seen.add(cmd)
        uniq.append(cmd)
    # uniq currently newest-first (because we iterated reversed), keep that order
    return uniq


def call_fzf(items, initial_query=None, use_custom_sort=False):
    """Open fzf interactive picker, optionally with an initial query."""
    fzf = shutil.which('fzf')
    if not fzf:
        return None
    try:
        # --tiebreak=index prefers items appearing earlier in the list
        cmd = [fzf, '--ansi', '--reverse', '--tiebreak=index']
        if use_custom_sort:
            # When we've pre-sorted, disable fzf's sorting
            cmd.append('--no-sort')
        if initial_query:
            cmd.extend(['--query', initial_query])
        p = subprocess.run(cmd, input='\n'.join(items), text=True, capture_output=True)
        if p.returncode != 0:
            return None
        return p.stdout.strip()
    except Exception:
        return None


def sort_by_similarity(query, items):
    """Sort items by fuzzy similarity to query, best matches first.
    
    Scoring prioritizes:
    1. Exact match (query == item)
    2. Starts with query (e.g., 'ls' matches 'ls -la' better than 'git ls-files')
    3. Query appears as whole word
    4. General fuzzy match
    """
    if not query:
        return items
    
    query_lower = query.lower()
    
    def score_item(item):
        item_lower = item.lower()
        
        # Exact match gets highest score
        if item_lower == query_lower:
            return (1000, 0)
        
        # Starts with query (command itself matches)
        if item_lower.startswith(query_lower + ' ') or item_lower.startswith(query_lower + '\t'):
            return (900, len(item))  # shorter commands rank higher
        
        # Exact match at start (no space needed for single-word commands)
        if item_lower == query_lower:
            return (900, 0)
            
        # Query is the first word/command
        first_word = item_lower.split()[0] if item_lower.split() else ''
        if first_word == query_lower:
            return (850, len(item))
        
        # First word starts with query
        if first_word.startswith(query_lower):
            return (800, len(item))
        
        # Query appears as a whole word somewhere
        words = item_lower.split()
        if query_lower in words:
            return (700, len(item))
        
        # Query is a substring at word boundary
        if f' {query_lower}' in item_lower or f'/{query_lower}' in item_lower:
            return (600, len(item))
        
        # General substring match
        if query_lower in item_lower:
            # Earlier position = better score
            pos = item_lower.index(query_lower)
            return (500 - pos, len(item))
        
        # Fuzzy match fallback
        fuzzy_score = fuzz.partial_ratio(query_lower, item_lower)
        return (fuzzy_score, len(item))
    
    # Sort by score descending, then by length ascending (shorter = better)
    scored = [(item, score_item(item)) for item in items]
    scored.sort(key=lambda x: (-x[1][0], x[1][1]))
    return [item for item, score in scored]


def fuzzy_search(query, items, limit=20):
    # use partial ratio for fuzzy substring-friendly matches
    results = process.extract(query, items, scorer=fuzz.partial_ratio, limit=limit)
    # results is list of (item, score, idx)
    return [item for item, score, idx in results]


def copy_to_clipboard(text):
    # macOS pbcopy
    try:
        p = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
        p.communicate(text.encode())
        return True
    except Exception:
        return False


def run_command(cmd):
    """Execute a command in a shell subprocess."""
    click.echo(f'Running: {cmd}', err=True)
    try:
        result = subprocess.run(cmd, shell=True)
        return result.returncode
    except Exception as e:
        click.echo(f'Error running command: {e}', err=True)
        return 1


@click.command()
@click.argument('query', required=False)
@click.option('-d', '--dry-run', is_flag=True, help='Dry run: print selected command without executing')
def main(query, dry_run):
    """AQS — fuzzy search recent commands.
    
    Opens fzf picker and executes the selected command.
    Use -d/--dry-run to only print without executing.
    """
    paths = detect_history_paths()
    items = read_history(paths)
    if not items:
        click.echo('No history found.', err=True)
        sys.exit(2)

    # If query provided, pre-sort by similarity so best matches appear first
    if query:
        items = sort_by_similarity(query, items)

    # Open fzf interactive picker (with optional initial query)
    # Use custom sort (--no-sort) only when we've pre-sorted with a query arg
    selected = call_fzf(items, initial_query=query, use_custom_sort=bool(query))
    
    if not selected:
        # fzf not available or user cancelled
        if not shutil.which('fzf'):
            click.echo('fzf not found. Install fzf: brew install fzf', err=True)
        sys.exit(1)

    # print selected command
    print(selected)
    
    # execute unless dry-run
    if not dry_run:
        sys.exit(run_command(selected))


if __name__ == '__main__':
    main()
