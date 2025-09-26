# v-and-r (Version and Release Manager)

- Version v0.2.0

A command-line tool that automates version management and release processes across multiple project files. The tool follows semantic versioning principles, integrates with git for release management, and ensures version consistency across all configured files in a project.

## Features

- **Version Discovery**: Scans configured files to find and display current versions
- **Semantic Versioning**: Supports patch, minor, and major version increments following semver
- **Multi-file Updates**: Updates version numbers across multiple files using configurable patterns
- **Release Management**: Generates release notes and compares commits between versions
- **Git Integration**: Leverages git tags and commit history for release tracking
- **Flexible Configuration**: Supports glob patterns and regex matching for diverse project structures

## Installation

Simply download the `v-and-r.py` script and make it executable:

```bash
# Download the script
curl -O https://raw.githubusercontent.com/your-repo/v-and-r.py

# Make it executable
chmod +x v-and-r.py

# Optionally, create a symlink for easier access
ln -s $(pwd)/v-and-r.py /usr/local/bin/v-and-r
```

## Quick Start

1. **View current versions with next patch version** (default behavior):
   ```bash
   python v-and-r.py
   # or
   python v-and-r.py --view
   
   # Show next minor version instead
   python v-and-r.py --view --minor
   
   # Show next major version instead  
   python v-and-r.py --view --major
   ```

2. **Increment patch version** (e.g., v1.2.3 → v1.2.4):
   ```bash
   python v-and-r.py --patch
   ```

3. **Increment minor version** (e.g., v1.2.3 → v1.3.0):
   ```bash
   python v-and-r.py --minor
   ```

4. **Generate release information**:
   ```bash
   python v-and-r.py --release-info
   ```

> **Note:** The `--view` command now shows comprehensive project information including:
> - Current versions across all configured files
> - Next version preview (patch by default, or specify `-mi`/`-ma` for minor/major)
> - Last git tag and commits since that tag (when in a git repository)
> - Working directory status: staged files, modified files, and untracked files
> - Contributor information and commit statistics
> 
> You can combine `--view` with increment flags (`-p`, `-mi`, `-ma`) to preview what the next version would be without actually modifying any files. When increment flags are used without `--view`, they perform the actual version increment.

## Command Reference

| Command | Short | Description |
|---------|-------|-------------|
| `--view` | `-v` | Show current versions, next patch version, git history, and working directory status (default) |
| `--view --patch` | `-v -p` | Show current versions with next patch version and git info |
| `--view --minor` | `-v -mi` | Show current versions with next minor version and git info |
| `--view --major` | `-v -ma` | Show current versions with next major version and git info |
| `--patch` | `-p` | Increment patch version (bug fixes) |
| `--minor` | `-mi` | Increment minor version (new features) |
| `--major` | `-ma` | Increment major version (breaking changes) |
| `--release-info` | `-r` | Generate version.json and display release notes |
| `--release-diff tag1 [tag2]` | `-rd` | Show commits between two tags or from tag to HEAD |
| `--release-last` | `-rl` | Show commits since the last git tag |
| `--release-prepare` | `-rp` | Prepare release by updating version.json, CHANGELOG.md, and RELEASES.md |
| `--help` | `-h` | Display help information and usage examples |

## Configuration

The tool uses a `VERSION_FILES` configuration array embedded in the script. This array defines which files to scan and update, along with the patterns to match and templates for replacement.

### Configuration Structure

Each configuration entry must contain:
- **`file`**: File path or glob pattern (supports wildcards like `*.py`, `src/**/*.py`)
- **`pattern`**: Compiled regex pattern with version in the first capture group
- **`template`**: String template with `{version}` placeholder for replacement

### Example Configuration

```python
VERSION_FILES = [
    # README.md version badge
    {
        'file': 'README.md', 
        'pattern': re.compile(r'- Version (v\d+\.\d+\.\d+)'),
        'template': '- Version {version}',
    },
    
    # Python files with version variable
    {
        'file': 'src/*.py',
        'pattern': re.compile(r'version = "(v\d+\.\d+\.\d+)"'),
        'template': 'version = "{version}"',
    },
    
    # Package __init__.py files
    {
        'file': 'src/*/__init__.py',
        'pattern': re.compile(r'__version__ = "(v\d+\.\d+\.\d+)"'),
        'template': '__version__ = "{version}"',
    },
]
```

### Common Configuration Patterns

#### Python Projects
```python
# setup.py
{
    'file': 'setup.py',
    'pattern': re.compile(r'version="(v\d+\.\d+\.\d+)"'),
    'template': 'version="{version}"',
}

# pyproject.toml
{
    'file': 'pyproject.toml',
    'pattern': re.compile(r'version = "(v\d+\.\d+\.\d+)"'),
    'template': 'version = "{version}"',
}

# Module __init__.py
{
    'file': 'mypackage/__init__.py',
    'pattern': re.compile(r'__version__ = "(v\d+\.\d+\.\d+)"'),
    'template': '__version__ = "{version}"',
}
```

#### Node.js Projects
```python
# package.json
{
    'file': 'package.json',
    'pattern': re.compile(r'"version": "(v\d+\.\d+\.\d+)"'),
    'template': '"version": "{version}"',
}
```

#### Docker Projects
```python
# Dockerfile
{
    'file': 'Dockerfile',
    'pattern': re.compile(r'LABEL version="(v\d+\.\d+\.\d+)"'),
    'template': 'LABEL version="{version}"',
}
```

#### Configuration Files
```python
# YAML configuration
{
    'file': 'config/*.yaml',
    'pattern': re.compile(r'version: (v\d+\.\d+\.\d+)'),
    'template': 'version: {version}',
}

# JSON configuration
{
    'file': 'config.json',
    'pattern': re.compile(r'"version": "(v\d+\.\d+\.\d+)"'),
    'template': '"version": "{version}"',
}
```

## Usage Examples

### Basic Version Management

```bash
# Check current versions
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

### Release Management

```bash
# Generate release information
python v-and-r.py --release-info
# Creates version.json with release metadata and displays release notes

# Compare commits between two releases
python v-and-r.py --release-diff v1.2.0 v1.3.0
# Shows all commits between the specified tags

# Show commits from a tag to current HEAD
python v-and-r.py --release-diff v1.2.0
# Shows all commits since the specified tag

# Show commits since last release
python v-and-r.py --release-last
# Shows commits from the last git tag to HEAD

# Prepare comprehensive release documentation
python v-and-r.py --release-prepare
# Updates version.json, CHANGELOG.md, and RELEASES.md
```

### Git Integration

The tool automatically integrates with git when available:

- **Tag Detection**: Finds and sorts git tags by semantic version
- **Commit History**: Analyzes commits between releases
- **Release Notes**: Generates release notes from commit messages
- **Graceful Degradation**: Works without git (limited functionality)

## File Formats

### version.json
Generated by `--release-info` and `--release-prepare` commands:

```json
{
  "version": "v1.2.3",
  "timestamp": "2023-01-01T10:00:00",
  "commit_hash": "abc1234",
  "previous_version": "v1.2.2",
  "commits": [
    {
      "hash": "abc1234567",
      "message": "feat: add new feature",
      "author": "Developer Name",
      "date": "2023-01-01T10:00:00"
    }
  ]
}
```

### CHANGELOG.md
Automatically updated by `--release-prepare`:

```markdown
# Changelog
All notable changes to this project will be documented here.

## [Unreleased]

## [v1.2.3] - 2023-01-01
### Added
- New feature implementation

### Fixed
- Bug fix for issue #123

### Commits
abc1234 feat: add new feature                                    Developer Name    2023-01-01 10:00 +0000
def5678 fix: resolve issue #123                                  Developer Name    2023-01-01 11:00 +0000
```

### RELEASES.md
Summary of releases updated by `--release-prepare`:

```markdown
# Releases

## v1.2.3 - 2023-01-01

**2 commits** from **1 contributors**

Changes since v1.2.2:
- 1 new features, 1 bug fixes

**Contributors:** Developer Name
**Commit Hash:** `abc1234`

### Highlights
- New feature implementation
- Bug fix for issue #123
```

## Troubleshooting

### Common Issues

#### "No versions found in configured files"
**Cause**: The regex patterns don't match the version format in your files.

**Solutions**:
1. Check that your version format matches the regex pattern (e.g., `v1.2.3` vs `1.2.3`)
2. Verify the regex pattern has a capture group: `(v\d+\.\d+\.\d+)`
3. Test your regex pattern with a regex tester
4. Use `--view` to see which files are being scanned

#### "Pattern must have at least one capture group"
**Cause**: The regex pattern doesn't include parentheses around the version.

**Solution**: Add parentheses around the version part:
```python
# Wrong
'pattern': re.compile(r'version = "v\d+\.\d+\.\d+"')

# Correct
'pattern': re.compile(r'version = "(v\d+\.\d+\.\d+)"')
```

#### "Template must contain {version} placeholder"
**Cause**: The template string is missing the `{version}` placeholder.

**Solution**: Include `{version}` in your template:
```python
# Wrong
'template': 'version = "1.0.0"'

# Correct
'template': 'version = "{version}"'
```

#### "No files match the pattern"
**Cause**: The file glob pattern doesn't match any existing files.

**Solutions**:
1. Check file paths are correct relative to where you run the script
2. Verify glob patterns: `*.py` (current directory), `src/*.py` (src directory)
3. Use absolute paths if needed
4. Check file permissions

#### "Git command failed" or "Not in a git repository"
**Cause**: Git is not available or the current directory is not a git repository.

**Solutions**:
1. Initialize git repository: `git init`
2. Install git if not available
3. Run the command from within a git repository
4. Some features work without git (version management still functions)

#### "Cannot write to file"
**Cause**: File permissions or file is locked by another process.

**Solutions**:
1. Check file permissions: `chmod 644 filename`
2. Ensure files are not open in editors
3. Run with appropriate permissions
4. Check disk space

### Debugging Tips

1. **Use `--view` first**: Always check what versions are detected before making changes
2. **Test regex patterns**: Use online regex testers to verify your patterns work
3. **Check file paths**: Ensure glob patterns match your project structure
4. **Backup files**: Consider version control or backups before bulk updates
5. **Start simple**: Begin with one file pattern and expand gradually

### Validation Errors

The tool validates configuration on startup. Common validation errors:

- **Empty configuration**: Add at least one file pattern
- **Missing required keys**: Ensure each entry has `file`, `pattern`, and `template`
- **Invalid regex**: Use `re.compile()` for pattern compilation
- **No capture groups**: Regex must capture the version in parentheses
- **Missing placeholder**: Template must include `{version}`

### Performance Considerations

- **Large repositories**: Use specific patterns instead of `**/*` wildcards
- **Many files**: Consider splitting configuration for different file types
- **Network drives**: File operations may be slower on network storage
- **Git operations**: Large repositories may have slower git history analysis

## Advanced Usage

### Custom Version Formats

The tool supports various version formats as long as they follow semantic versioning:

```python
# With 'v' prefix (recommended)
'pattern': re.compile(r'version = "(v\d+\.\d+\.\d+)"')

# Without 'v' prefix
'pattern': re.compile(r'version = "(\d+\.\d+\.\d+)"')

# In comments
'pattern': re.compile(r'# Version: (v\d+\.\d+\.\d+)')

# In YAML
'pattern': re.compile(r'version: (v\d+\.\d+\.\d+)')
```

### Multiple Patterns per File Type

You can have multiple configuration entries for the same file pattern:

```python
VERSION_FILES = [
    # Match both quoted and unquoted versions in Python files
    {
        'file': '*.py',
        'pattern': re.compile(r'version = "(v\d+\.\d+\.\d+)"'),
        'template': 'version = "{version}"',
    },
    {
        'file': '*.py',
        'pattern': re.compile(r'VERSION = (v\d+\.\d+\.\d+)'),
        'template': 'VERSION = {version}',
    },
]
```

### Recursive Directory Patterns

Use glob patterns for recursive directory scanning:

```python
{
    'file': 'src/**/*.py',  # All Python files in src and subdirectories
    'pattern': re.compile(r'__version__ = "(v\d+\.\d+\.\d+)"'),
    'template': '__version__ = "{version}"',
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## Roadmap
- [x] Issue: missing `--release-deploy` execute the git tag v1.0.0 -m "Release Name"
- [x] Issue: missing `-rd TAG` get the last commits from TAG to HEAD
- [x] Add Next version in --view with -p or -mi or -ma (use -p as default)
- [ ] Improve `--view` output 🚧
- [ ] Add --release-prepare  with -p or -mi or -ma and use Next version (use -p as default)
- [ ] Make commit before tag
- [ ] Move documentation to /docs dir
- [ ] Change test message 'Some tests failed! ✗' for 'Tests failed: none 😀'
- [ ] Add usefull commands
    - custom list of commits
    - custom list of tags
- [ ] Add Release Name generator for major and minor releases
- [ ] Add support for pre-release and build metadata (e.g., v1.0.0-alpha, v1.0.0+build.1)
- [ ] Add `--dry-run` flag for testing changes without applying them
- [ ] Add `--log` option to log operations to system log
- [ ] Improve even more the `--view` output
- [ ] Support external configuration files (.v-and-r.json or .v-and-r.yaml)
- [ ] Add plugin system for custom version increment strategies
- [ ] Support for monorepo version management
- [ ] Integration with CI/CD pipelines
- [ ] Web interface for release management

## License

MIT License - see LICENSE file for details.


# Modified content
