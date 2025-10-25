# Technology Stack

## Coding rules
- Avoid onliners for simplicity and maintainability
- Avoid Context manager

## Language & Runtime
- **Python 3.x**: Primary development language for prototype 
    - **Type Hinting**: Used for improved code readability and maintainability
- **C**: for executable
- **Command-line interface**: Built as a CLI tool using argparse or similar

## Core Dependencies
- **Standard Library**: 
  - `re` for regex pattern matching
  - `argparse` for command-line argument parsing
  - `json` for version.json generation
  - `os`/`pathlib` for file system operations
  - `glob` for wildcard file matching
- **Git Integration**: 
  - `subprocess` or `GitPython` for git operations
  - Git tags for version tracking
  - Commit history analysis

## Architecture Patterns
- **Configuration-driven**: Uses VERSION_FILES array for flexible file pattern definitions
- **Semantic Versioning**: Follows semver (major.minor.patch) format with 'v' prefix
- **Template-based Updates**: Uses string templates with {version} placeholders
- **Regex Pattern Matching**: First capture group contains the version number

## Common Commands
```bash
# Development
python grtp.py --help          # View all options
python grtp.py --view          # Check current versions
python grtp.py --patch         # Increment patch version

# Testing version patterns
python grtp.py --view          # Verify pattern matching works

# Release workflow
python grtp.py --minor         # Bump minor version
python grtp.py --release-info  # Generate release notes
```

## File Processing
- Supports glob patterns (*.py, directory/*.py)
- Regex patterns must capture version in first group
- Template strings use {version} placeholder for replacements