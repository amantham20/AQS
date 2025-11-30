# Deprecated Python Version

This folder contains the original Python implementation of AQS.

**This version is deprecated.** The project has been rewritten in Go for better performance.

## Why Deprecated?

- Python startup time was too slow
- Required Python runtime + packages (click, rapidfuzz)
- PyInstaller binaries were large and slow to start

## New Go Version

The new Go version:
- Compiles to a fast native binary
- No runtime dependencies (except fzf)
- Instant startup
- Much smaller binary size

See the main README for installation instructions.
