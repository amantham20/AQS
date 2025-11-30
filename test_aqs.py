#!/usr/bin/env python3
"""Tests for AQS CLI tool."""

import pytest
import sys
sys.path.insert(0, '.')

from aqs import sort_by_similarity, read_history, detect_history_paths


class TestSortBySimilarity:
    """Test the sort_by_similarity function."""
    
    def test_exact_match_first(self):
        """Exact match should rank highest."""
        items = ['ls -la', 'git ls-files', 'ls', 'echo ls']
        result = sort_by_similarity('ls', items)
        assert result[0] == 'ls', f"Expected 'ls' first, got {result}"
    
    def test_starts_with_query_ranks_high(self):
        """Commands starting with query should rank high."""
        items = ['git ls-files', 'ls -la', 'ls -l', 'echo hello']
        result = sort_by_similarity('ls', items)
        # 'ls -la' and 'ls -l' should come before 'git ls-files'
        ls_commands = [r for r in result[:2] if r.startswith('ls')]
        assert len(ls_commands) == 2, f"Expected ls commands first, got {result}"
    
    def test_shorter_commands_preferred(self):
        """Among similar matches, shorter commands should rank higher."""
        items = ['ls -la --color=auto', 'ls -la', 'ls -l', 'ls']
        result = sort_by_similarity('ls', items)
        assert result[0] == 'ls', f"Expected 'ls' first, got {result}"
        assert result[1] == 'ls -l', f"Expected 'ls -l' second, got {result}"
    
    def test_first_word_match(self):
        """Query matching first word should rank high."""
        items = ['cd /some/path', 'git commit', 'git push', 'echo git']
        result = sort_by_similarity('git', items)
        git_first = [r for r in result[:2] if r.startswith('git')]
        assert len(git_first) == 2, f"Expected git commands first, got {result}"
    
    def test_substring_match(self):
        """Substring matches should still appear."""
        items = ['echo hello', 'cat file.txt', 'grep pattern', 'history']
        result = sort_by_similarity('hist', items)
        assert 'history' in result, f"Expected 'history' in results, got {result}"
    
    def test_no_query_returns_unchanged(self):
        """Empty query should return items unchanged."""
        items = ['ls', 'cd', 'git']
        result = sort_by_similarity('', items)
        assert result == items
        
        result = sort_by_similarity(None, items)
        assert result == items
    
    def test_case_insensitive(self):
        """Matching should be case insensitive."""
        items = ['LS -la', 'Git Push', 'ECHO hello']
        result = sort_by_similarity('git', items)
        assert result[0] == 'Git Push', f"Expected 'Git Push' first, got {result}"
    
    def test_word_boundary_match(self):
        """Query at word boundary should rank higher than mid-word."""
        items = ['flashlight', 'ls -la', 'als']
        result = sort_by_similarity('ls', items)
        assert result[0] == 'ls -la', f"Expected 'ls -la' first, got {result}"
    
    def test_complex_commands(self):
        """Test with realistic complex commands."""
        items = [
            'git add -A && git commit -m "message" && git push',
            'git status',
            'git log --oneline',
            'ls -la',
            'echo "git is great"',
        ]
        result = sort_by_similarity('git', items)
        # All git commands should come before non-git commands
        git_cmds = [r for r in result if r.startswith('git')]
        non_git = [r for r in result if not r.startswith('git')]
        
        # Git commands should all be before non-git in the result
        last_git_idx = max(result.index(cmd) for cmd in git_cmds)
        first_non_git_idx = min(result.index(cmd) for cmd in non_git)
        assert last_git_idx < first_non_git_idx, f"Git commands should rank before non-git: {result}"
    
    def test_docker_commands(self):
        """Test docker command sorting."""
        items = [
            'docker ps',
            'docker-compose up',
            'docker build -t myapp .',
            'sudo docker ps -a',
            'echo docker',
        ]
        result = sort_by_similarity('docker', items)
        # 'docker ps' should be first (starts with docker, shortest)
        assert result[0] == 'docker ps', f"Expected 'docker ps' first, got {result}"
    
    def test_path_commands(self):
        """Test commands with paths."""
        items = [
            'cd /Users/test/projects',
            'cd ~',
            'cd ..',
            '/usr/bin/cd somewhere',
        ]
        result = sort_by_similarity('cd', items)
        # Commands starting with 'cd' should come first
        assert result[0].startswith('cd'), f"Expected cd command first, got {result}"
    
    def test_pip_install(self):
        """Test pip commands."""
        items = [
            'pip install requests',
            'pip install -r requirements.txt',
            'pip freeze',
            'python -m pip install flask',
        ]
        result = sort_by_similarity('pip install', items)
        # Exact 'pip install' prefix should rank highest
        assert 'pip install' in result[0], f"Expected pip install first, got {result}"


class TestReadHistory:
    """Test history reading functionality."""
    
    def test_deduplication(self):
        """Test that duplicate commands are removed."""
        # This tests the deduplication logic
        # We can't easily test file reading, but we can verify the logic
        pass  # Would need mock files
    
    def test_detect_history_paths(self):
        """Test that history paths are detected."""
        paths = detect_history_paths()
        assert len(paths) > 0, "Should detect at least one history path"
        
        # Test specific shell
        bash_paths = detect_history_paths('bash')
        assert any('.bash_history' in str(p) for p in bash_paths)
        
        zsh_paths = detect_history_paths('zsh')
        assert any('.zsh_history' in str(p) for p in zsh_paths)
        
        fish_paths = detect_history_paths('fish')
        assert any('fish_history' in str(p) for p in fish_paths)


class TestEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_empty_items(self):
        """Empty items list should return empty."""
        result = sort_by_similarity('ls', [])
        assert result == []
    
    def test_special_characters(self):
        """Commands with special characters should work."""
        items = [
            'echo "hello world"',
            'grep -E "^test.*$"',
            "awk '{print $1}'",
            'ls | grep test',
        ]
        result = sort_by_similarity('grep', items)
        assert 'grep -E "^test.*$"' in result[:2], f"Expected grep command in top 2, got {result}"
    
    def test_very_long_commands(self):
        """Very long commands should still work."""
        long_cmd = 'git add -A && git commit -m "' + 'a' * 1000 + '" && git push'
        items = ['git status', long_cmd, 'ls']
        result = sort_by_similarity('git', items)
        assert result[0] == 'git status', f"Shorter git command should rank first, got {result}"
    
    def test_numbers_in_query(self):
        """Queries with numbers should work."""
        items = ['python3 script.py', 'python2 old.py', 'python main.py']
        result = sort_by_similarity('python3', items)
        assert result[0] == 'python3 script.py', f"Expected python3 first, got {result}"
    
    def test_single_character_query(self):
        """Single character queries should work."""
        items = ['ls', 'cd', 'cat', 'a']
        result = sort_by_similarity('a', items)
        assert result[0] == 'a', f"Expected 'a' first, got {result}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
