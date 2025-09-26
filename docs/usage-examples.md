# 💡 Usage Examples

## Basic Version Management

### Viewing Current Versions

```bash
# Check current versions with comprehensive project overview
python v-and-r.py --view
# Output:
# Current versions across configured files:
# README.md: v1.2.3
# src/app.py: v1.2.3
# src/__init__.py: v1.2.3
# Highest version: v1.2.3
# Next patch version: v1.2.4
# 
# Git Information:
# Last tag: v1.2.0
# Commits since v1.2.0 (3 commits):
# abc1234  Fix critical bug in authentication
# def5678  Update documentation  
# ghi9012  Refactor user management
# Total commits since v1.2.0: 3
#
# Working Directory Status:
# Changes not staged for commit:
#   modified:   src/app.py
# Untracked files:
#   new-feature.py
# Summary: 1 changed file, 1 untracked file

# View with different next version types
python v-and-r.py --view --minor    # Shows next minor version
python v-and-r.py --view --major    # Shows next major version
```

### Version Increments

```bash
# Increment patch version for bug fix
python v-and-r.py --patch
# Output:
# Found highest version: v1.2.3
# New version: v1.2.4
# Updated README.md: v1.2.3 → v1.2.4 ✓
# Updated src/app.py: v1.2.3 → v1.2.4 ✓
# Updated src/__init__.py: v1.2.3 → v1.2.4 ✓
# Version increment completed successfully!

# Increment minor version for new feature
python v-and-r.py --minor
# Output: v1.2.4 → v1.3.0

# Increment major version for breaking changes
python v-and-r.py --major
# Output: v1.3.0 → v2.0.0
```

## Release Management

### Generating Release Information

```bash
# Generate release information
python v-and-r.py --release-info
# Creates version.json with release metadata and displays release notes
```

### Comparing Releases

```bash
# Compare commits between two releases
python v-and-r.py --release-diff v1.2.0 v1.3.0
# Shows all commits between the specified tags

# Show commits from a tag to current HEAD
python v-and-r.py --release-diff v1.2.0
# Shows all commits since the specified tag

# Show commits since last release
python v-and-r.py --release-last
# Shows commits from the last git tag to HEAD
```

### Preparing Releases

```bash
# Prepare comprehensive release documentation
python v-and-r.py --release-prepare
# Updates version.json, CHANGELOG.md, and RELEASES.md

# Deploy release with git tag
python v-and-r.py --release-deploy
# Creates git tag for current version

# Deploy with custom message
python v-and-r.py --release-deploy -m "Release v1.2.3 with new features"
# Creates annotated git tag with custom message
```

## Common Workflows

### Bug Fix Release Workflow

```bash
# 1. Check current status
python v-and-r.py --view

# 2. Make your bug fixes
# ... edit code ...

# 3. Increment patch version
python v-and-r.py --patch

# 4. Prepare release documentation
python v-and-r.py --release-prepare

# 5. Deploy release
python v-and-r.py --release-deploy -m "Bug fix release v1.2.4"

# 6. Push changes and tags
git push origin main
git push origin v1.2.4
```

### Feature Release Workflow

```bash
# 1. Check what's changed since last release
python v-and-r.py --release-last

# 2. Preview next minor version
python v-and-r.py --view --minor

# 3. Increment minor version
python v-and-r.py --minor

# 4. Prepare release documentation
python v-and-r.py --release-prepare

# 5. Deploy release
python v-and-r.py --release-deploy -m "Feature release v1.3.0"
```

### Major Release Workflow

```bash
# 1. Review all changes since last major release
python v-and-r.py --release-diff v1.0.0

# 2. Preview next major version
python v-and-r.py --view --major

# 3. Increment major version
python v-and-r.py --major

# 4. Prepare comprehensive release documentation
python v-and-r.py --release-prepare

# 5. Deploy major release
python v-and-r.py --release-deploy -m "Major release v2.0.0 with breaking changes"
```

### Pre-release Workflow

```bash
# 1. Check current development status
python v-and-r.py --view

# 2. See what's changed since last release
python v-and-r.py --release-last

# 3. Generate release information for review
python v-and-r.py --release-info

# 4. When ready, increment version and deploy
python v-and-r.py --minor
python v-and-r.py --release-deploy
```

## Git Integration Examples

### Working with Git Tags

```bash
# List all version tags
git tag -l | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$'

# Compare with v-and-r's tag detection
python v-and-r.py --view

# Show commits between any two tags
python v-and-r.py --release-diff v1.0.0 v1.5.0
```

### Branch-based Development

```bash
# On feature branch
git checkout feature/new-feature

# Check current version (doesn't modify)
python v-and-r.py --view

# After merging to main
git checkout main
git merge feature/new-feature

# Increment version and release
python v-and-r.py --minor
python v-and-r.py --release-deploy
```

## Multi-Project Examples

### Monorepo Management

```bash
# Different configurations for different components
cd backend/
python ../v-and-r.py --patch  # Backend bug fix

cd ../frontend/
python ../v-and-r.py --minor  # Frontend new feature

cd ../
python v-and-r.py --view      # Overall project status
```

### Coordinated Releases

```bash
# Release multiple components together
python v-and-r.py --minor                    # Increment version
python v-and-r.py --release-prepare          # Update documentation
python v-and-r.py --release-deploy -m "Coordinated release v1.3.0"
```

## Automation Examples

### CI/CD Integration

```bash
#!/bin/bash
# release.sh - Automated release script

# Check if working directory is clean
if ! python v-and-r.py --view | grep -q "Working directory clean"; then
    echo "Error: Working directory not clean"
    exit 1
fi

# Increment version based on commit messages
if git log --oneline $(git describe --tags --abbrev=0)..HEAD | grep -q "BREAKING CHANGE"; then
    python v-and-r.py --major
elif git log --oneline $(git describe --tags --abbrev=0)..HEAD | grep -q "feat:"; then
    python v-and-r.py --minor
else
    python v-and-r.py --patch
fi

# Prepare and deploy release
python v-and-r.py --release-prepare
python v-and-r.py --release-deploy -m "Automated release"

# Push changes
git push origin main --tags
```

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Check version consistency
if ! python v-and-r.py --view > /dev/null 2>&1; then
    echo "Error: Version inconsistency detected"
    echo "Run 'python v-and-r.py --view' to see details"
    exit 1
fi
```

## Troubleshooting Examples

### Debugging Configuration

```bash
# Test if patterns match
python v-and-r.py --view

# Check specific files
grep -n "version" src/app.py
python -c "import re; print(re.compile(r'version = \"(v\d+\.\d+\.\d+)\"').search('version = \"v1.2.3\"'))"
```

### Fixing Version Mismatches

```bash
# Find all versions in project
python v-and-r.py --view

# Manually fix inconsistent versions
# Edit files to match highest version

# Verify fix
python v-and-r.py --view
```

### Recovery from Errors

```bash
# If version increment fails, check git status
git status

# Restore from git if needed
git checkout -- .

# Fix configuration and retry
python v-and-r.py --patch
```