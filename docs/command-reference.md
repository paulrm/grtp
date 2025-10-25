# 📚 Command Reference

## Overview

grtp provides a comprehensive command-line interface for version management and release operations.

## Command Syntax

```bash
python grtp.py [COMMAND] [OPTIONS]
```

## Commands

### View Commands

#### `--view` / `-v`
Show current versions, next patch version, git history, and working directory status (default behavior).

```bash
python grtp.py --view
python grtp.py -v

# With next version preview
python grtp.py --view --patch    # Next patch version (default)
python grtp.py --view --minor    # Next minor version
python grtp.py --view --major    # Next major version
```

**Output includes:**
- Current versions across all configured files
- Highest version detected
- Next version preview
- Last git tag and commits since that tag
- Working directory status (staged, modified, untracked files)
- Contributor information and statistics

### Version Increment Commands

#### `--patch` / `-p`
Increment patch version (e.g., v1.2.3 → v1.2.4) for bug fixes.

```bash
python grtp.py --patch
python grtp.py -p
```

#### `--minor` / `-mi`
Increment minor version and reset patch (e.g., v1.2.3 → v1.3.0) for new features.

```bash
python grtp.py --minor
python grtp.py -mi
```

#### `--major` / `-ma`
Increment major version and reset minor/patch (e.g., v1.2.3 → v2.0.0) for breaking changes.

```bash
python grtp.py --major
python grtp.py -ma
```

### Release Management Commands

#### `--release-info` / `-r`
Generate release information and version.json file.

```bash
python grtp.py --release-info
python grtp.py -r
```

**Generates:**
- version.json with release metadata
- Release notes from commit history
- Contributor statistics

#### `--release-diff` / `-rd`
Show commits between two git tags or from tag to HEAD.

```bash
# Between two tags
python grtp.py --release-diff v1.0.0 v1.1.0
python grtp.py -rd v1.0.0 v1.1.0

# From tag to HEAD
python grtp.py --release-diff v1.0.0
python grtp.py -rd v1.0.0
```

#### `--release-last` / `-rl`
Show commits since the last git tag.

```bash
python grtp.py --release-last
python grtp.py -rl
```

#### `--release-prepare` / `-rp`
Prepare release by updating version.json, CHANGELOG.md, and RELEASES.md.

```bash
python grtp.py --release-prepare
python grtp.py -rp
```

**Updates:**
- version.json with current release information
- CHANGELOG.md with new entries
- RELEASES.md with release summary

#### `--release-deploy`
Create git tag for current version to deploy release.

```bash
# Create lightweight tag
python grtp.py --release-deploy

# Create annotated tag with message
python grtp.py --release-deploy -m "Release v1.2.3 with new features"
```

### Options

#### `-m` / `--message`
Specify release message for annotated git tag (used with --release-deploy).

```bash
python grtp.py --release-deploy -m "Major release with breaking changes"
```

#### `-d` / `--debug`
Enable debug logging for troubleshooting.

```bash
python grtp.py --debug --view
```

#### `-h` / `--help`
Display help information and usage examples.

```bash
python grtp.py --help
```

## Command Combinations

### View with Next Version Preview

```bash
# Default: shows next patch version
python grtp.py

# Explicit patch version preview
python grtp.py --view --patch

# Minor version preview
python grtp.py --view --minor

# Major version preview
python grtp.py --view --major
```

### Release Workflow Commands

```bash
# Complete release workflow
python grtp.py --patch                    # 1. Increment version
python grtp.py --release-prepare          # 2. Update documentation
python grtp.py --release-deploy -m "Bug fix release"  # 3. Create tag
```

## Exit Codes

- **0**: Success
- **1**: General error (file operations, git errors, etc.)
- **2**: Configuration error
- **3**: Version error (parsing, validation)
- **4**: File error (permissions, not found)
- **5**: Git error (not a repository, command failed)

## Command Validation

### Mutually Exclusive Commands

These commands cannot be used together:
- Version increment commands (`--patch`, `--minor`, `--major`) when used without `--view`
- Release management commands (`--release-info`, `--release-diff`, etc.)

### Required Arguments

- `--release-diff` requires 1 or 2 tag arguments
- `--message` can only be used with `--release-deploy`

### Validation Errors

```bash
# Error: Multiple increment types
python grtp.py --patch --minor
# Error: Only one increment type (-p, -mi, -ma) can be specified at a time

# Error: Message without deploy
python grtp.py --release-info -m "message"
# Error: -m/--message option can only be used with --release-deploy

# Error: Invalid tag arguments
python grtp.py --release-diff
# Error: TAG must be provided for --release-diff

# Error: Same tags
python grtp.py --release-diff v1.0.0 v1.0.0
# Error: TAG1 and TAG2 cannot be the same for --release-diff
```

## Examples by Use Case

### Development Workflow

```bash
# Daily development
python grtp.py                           # Check status
python grtp.py --release-last            # See recent changes

# Bug fix
python grtp.py --patch                   # Increment patch
python grtp.py --release-deploy          # Deploy fix

# Feature development
python grtp.py --view --minor            # Preview next minor
python grtp.py --minor                   # Increment minor
python grtp.py --release-prepare         # Update docs
```

### Release Management

```bash
# Release preparation
python grtp.py --release-info            # Generate release info
python grtp.py --release-diff v1.0.0     # Review changes
python grtp.py --release-prepare         # Update documentation

# Release deployment
python grtp.py --release-deploy -m "Release v1.1.0"
```

### Debugging and Troubleshooting

```bash
# Debug mode
python grtp.py --debug --view            # Verbose output
python grtp.py --debug --patch           # Debug version increment

# Check configuration
python grtp.py --view                    # Verify patterns match
python grtp.py --help                    # Review usage
```