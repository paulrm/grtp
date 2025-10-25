# ⚙️ Configuration Guide

## Overview

grtp supports two configuration methods:

1. **External Configuration** (Recommended): `.grtp.json` file in your project root
2. **Embedded Configuration** (Fallback): `VERSION_FILES` array in the script

The tool automatically uses external configuration if available, otherwise falls back to embedded configuration.

## External Configuration (Recommended)

### Creating Configuration

Create a default configuration file:

```bash
grtp --init
```

This creates `.grtp.json` with default patterns for common file types.

### Configuration Structure

Each configuration entry must contain:
- **`file`**: File path or glob pattern (supports wildcards like `*.py`, `src/**/*.py`)
- **`pattern`**: Regex pattern string with version in the first capture group
- **`template`**: String template with `{version}` placeholder for replacement

### Example External Configuration

```json
{
  "VERSION_FILES": [
    {
      "file": "README.md",
      "pattern": "- Version v(\\d+\\.\\d+\\.\\d+)",
      "template": "- Version v{version}"
    },
    {
      "file": "src/*.py",
      "pattern": "version = \"v(\\d+\\.\\d+\\.\\d+)\"",
      "template": "version = \"v{version}\""
    },
    {
      "file": "src/*/__init__.py",
      "pattern": "__version__ = \"v(\\d+\\.\\d+\\.\\d+)\"",
      "template": "__version__ = \"v{version}\""
    }
  ]
}
```

## Embedded Configuration (Fallback)

If no `.grtp.json` file exists, the tool uses embedded configuration in `grtp.py`:

```python
def get_embedded_version_files_config() -> List[Dict]:
    return [
        {
            'file': 'README.md', 
            'pattern': re.compile(r'- Version v(\d+\.\d+\.\d+)'),
            'template': '- Version v{version}',
        },
        # ... more patterns
    ]
```

## Common Configuration Patterns

### Python Projects

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

### Node.js Projects

```python
# package.json
{
    'file': 'package.json',
    'pattern': re.compile(r'"version": "(v\d+\.\d+\.\d+)"'),
    'template': '"version": "{version}"',
}
```

### Docker Projects

```python
# Dockerfile
{
    'file': 'Dockerfile',
    'pattern': re.compile(r'LABEL version="(v\d+\.\d+\.\d+)"'),
    'template': 'LABEL version="{version}"',
}
```

### Configuration Files

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

## Advanced Configuration

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

## Configuration Validation

The tool validates configuration on startup. Common validation errors:

- **Empty configuration**: Add at least one file pattern
- **Missing required keys**: Ensure each entry has `file`, `pattern`, and `template`
- **Invalid regex**: Use `re.compile()` for pattern compilation
- **No capture groups**: Regex must capture the version in parentheses
- **Missing placeholder**: Template must include `{version}`

## Best Practices

1. **Start Simple**: Begin with one file pattern and expand gradually
2. **Test Patterns**: Use `--view` to verify patterns match correctly
3. **Use Capture Groups**: Always wrap the version in parentheses in regex
4. **Consistent Formatting**: Use consistent version format across files
5. **Backup First**: Test configuration on a backup or version-controlled project

## Example Configurations by Project Type

### Python Package

```python
VERSION_FILES = [
    {
        'file': 'setup.py',
        'pattern': re.compile(r'version="(v\d+\.\d+\.\d+)"'),
        'template': 'version="{version}"',
    },
    {
        'file': 'mypackage/__init__.py',
        'pattern': re.compile(r'__version__ = "(v\d+\.\d+\.\d+)"'),
        'template': '__version__ = "{version}"',
    },
    {
        'file': 'README.md',
        'pattern': re.compile(r'Version (v\d+\.\d+\.\d+)'),
        'template': 'Version {version}',
    },
]
```

### Node.js Application

```python
VERSION_FILES = [
    {
        'file': 'package.json',
        'pattern': re.compile(r'"version": "(v\d+\.\d+\.\d+)"'),
        'template': '"version": "{version}"',
    },
    {
        'file': 'src/version.js',
        'pattern': re.compile(r'export const VERSION = "(v\d+\.\d+\.\d+)"'),
        'template': 'export const VERSION = "{version}"',
    },
]
```

### Multi-language Project

```python
VERSION_FILES = [
    # Documentation
    {
        'file': 'README.md',
        'pattern': re.compile(r'Version (v\d+\.\d+\.\d+)'),
        'template': 'Version {version}',
    },
    # Python
    {
        'file': 'backend/**/*.py',
        'pattern': re.compile(r'__version__ = "(v\d+\.\d+\.\d+)"'),
        'template': '__version__ = "{version}"',
    },
    # JavaScript
    {
        'file': 'frontend/package.json',
        'pattern': re.compile(r'"version": "(v\d+\.\d+\.\d+)"'),
        'template': '"version": "{version}"',
    },
    # Docker
    {
        'file': 'Dockerfile',
        'pattern': re.compile(r'LABEL version="(v\d+\.\d+\.\d+)"'),
        'template': 'LABEL version="{version}"',
    },
]
```