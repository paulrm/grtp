# 📚 Command Reference

## Overview

v-and-r provides a comprehensive command-line interface for version management and release operations.

## Command Syntax

```bash
python v-and-r.py [COMMAND] [OPTIONS]
```

## Commands

### View Commands

#### `--view` / `-v`
Show current versions, next patch version, git history, and working directory status (default behavior).

```bash
python v-and-r.py --view
python v-and-r.py -v

# With next version preview
python v-and-r.py --view --patch    # Next patch version (default)
python v-and-r.py --view --minor    # Next minor version
python v-and-r.py --view --major    # Next major version
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
python v-and-r.py --patch
python v-and-r.py -p
```

#### `--minor` / `-mi`
Increment minor version and reset patch (e.g., v1.2.3 → v1.3.0) for new features.

```bash
python v-and-r.py --minor
python v-and-r.py -mi
```

#### `--major` / `-ma`
Increment major version and reset minor/patch (e.g., v1.2.3 → v2.0.0) for breaking changes.

```bash
python v-and-r.py --major
python v-and-r.py -ma
```

### Release Management Commands

#### `--release-info` / `-r`
Generate release information and version.json file.

```bash
python v-and-r.py --release-info
python v-and-r.py -r
```

**Generates:**
- version.json with release metadata
- Release notes from commit history
- Contributor statistics

#### `--release-diff` / `-rd`
Show commits between two git tags or from tag to HEAD.

```bash
# Between two tags
python v-and-r.py --release-diff v1.0.0 v1.1.0
python v-and-r.py -rd v1.0.0 v1.1.0

# From tag to HEAD
python v-and-r.py --release-diff v1.0.0
python v-and-r.py -rd v1.0.0
```

#### `--release-last` / `-rl`
Show commits since the last git tag.

```bash
python v-and-r.py --release-last
python v-and-r.py -rl
```

#### `--release-prepare` / `-rp`
Prepare release by updating version.json, CHANGELOG.md, and RELEASES.md.

```bash
python v-and-r.py --release-prepare
python v-and-r.py -rp
```

**Updates:**
- version.json with current release information
- CHANGELOG.md with new entries
- RELEASES.md with release summary

#### `--release-deploy`
Create git tag for current version to deploy release.

```bash
# Create lightweight tag
python v-and-r.py --release-deploy

# Create annotated tag with message
python v-and-r.py --release-deploy -m "Release v1.2.3 with new features"
```

### Options

#### `-m` / `--message`
Specify release message for annotated git tag (used with --release-deploy).

```bash
python v-and-r.py --release-deploy -m "Major release with breaking changes"
```

#### `-d` / `--debug`
Enable debug logging for troubleshooting.

```bash
python v-and-r.py --debug --view
```

#### `-h` / `--help`
Display help information and usage examples.

```bash
python v-and-r.py --help
```

## Command Combinations

### View with Next Version Preview

```bash
# Default: shows next patch version
python v-and-r.py

# Explicit patch version preview
python v-and-r.py --view --patch

# Minor version preview
python v-and-r.py --view --minor

# Major version preview
python v-and-r.py --view --major
```

### Release Workflow Commands

```bash
# Complete release workflow
python v-and-r.py --patch                    # 1. Increment version
python v-and-r.py --release-prepare          # 2. Update documentation
python v-and-r.py --release-deploy -m "Bug fix release"  # 3. Create tag
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
python v-and-r.py --patch --minor
# Error: Only one increment type (-p, -mi, -ma) can be specified at a time

# Error: Message without deploy
python v-and-r.py --release-info -m "message"
# Error: -m/--message option can only be used with --release-deploy

# Error: Invalid tag arguments
python v-and-r.py --release-diff
# Error: TAG must be provided for --release-diff

# Error: Same tags
python v-and-r.py --release-diff v1.0.0 v1.0.0
# Error: TAG1 and TAG2 cannot be the same for --release-diff
```

## Examples by Use Case

### Development Workflow

```bash
# Daily development
python v-and-r.py                           # Check status
python v-and-r.py --release-last            # See recent changes

# Bug fix
python v-and-r.py --patch                   # Increment patch
python v-and-r.py --release-deploy          # Deploy fix

# Feature development
python v-and-r.py --view --minor            # Preview next minor
python v-and-r.py --minor                   # Increment minor
python v-and-r.py --release-prepare         # Update docs
```

### Release Management

```bash
# Release preparation
python v-and-r.py --release-info            # Generate release info
python v-and-r.py --release-diff v1.0.0     # Review changes
python v-and-r.py --release-prepare         # Update documentation

# Release deployment
python v-and-r.py --release-deploy -m "Release v1.1.0"
```

### Debugging and Troubleshooting

```bash
# Debug mode
python v-and-r.py --debug --view            # Verbose output
python v-and-r.py --debug --patch           # Debug version increment

# Check configuration
python v-and-r.py --view                    # Verify patterns match
python v-and-r.py --help                    # Review usage
```