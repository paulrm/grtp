# 🚀 Advanced Usage

## Custom Version Formats

### Non-standard Version Patterns

While grtp follows semantic versioning by default, you can customize it for different formats:

```python
# Date-based versions
{
    'file': 'version.txt',
    'pattern': re.compile(r'(\d{4}\.\d{2}\.\d{2})'),
    'template': '{version}',
}

# Build numbers
{
    'file': 'build.properties',
    'pattern': re.compile(r'build\.number=(\d+)'),
    'template': 'build.number={version}',
}

# Custom prefixes
{
    'file': 'app.config',
    'pattern': re.compile(r'AppVersion=(release-v\d+\.\d+\.\d+)'),
    'template': 'AppVersion={version}',
}
```

### Version Format Validation

Create custom validation for your version formats:

```python
def validate_custom_version(version_string):
    """Custom version validation"""
    import re
    
    # Date-based version: YYYY.MM.DD
    date_pattern = re.compile(r'^\d{4}\.\d{2}\.\d{2}$')
    if date_pattern.match(version_string):
        return True
    
    # Semantic version with custom prefix
    semver_pattern = re.compile(r'^release-v\d+\.\d+\.\d+$')
    if semver_pattern.match(version_string):
        return True
    
    return False
```

## Complex Configuration Scenarios

### Multi-Environment Configuration

```python
VERSION_FILES = [
    # Production configuration
    {
        'file': 'config/production.yaml',
        'pattern': re.compile(r'version: (v\d+\.\d+\.\d+)'),
        'template': 'version: {version}',
    },
    
    # Staging configuration
    {
        'file': 'config/staging.yaml',
        'pattern': re.compile(r'version: (v\d+\.\d+\.\d+)'),
        'template': 'version: {version}',
    },
    
    # Development configuration
    {
        'file': 'config/development.yaml',
        'pattern': re.compile(r'version: (v\d+\.\d+\.\d+)'),
        'template': 'version: {version}',
    },
]
```

### Conditional File Processing

```python
import os

VERSION_FILES = []

# Add configuration based on environment
if os.path.exists('package.json'):
    # Node.js project
    VERSION_FILES.append({
        'file': 'package.json',
        'pattern': re.compile(r'"version": "(v\d+\.\d+\.\d+)"'),
        'template': '"version": "{version}"',
    })

if os.path.exists('setup.py'):
    # Python project
    VERSION_FILES.append({
        'file': 'setup.py',
        'pattern': re.compile(r'version="(v\d+\.\d+\.\d+)"'),
        'template': 'version="{version}"',
    })

if os.path.exists('Cargo.toml'):
    # Rust project
    VERSION_FILES.append({
        'file': 'Cargo.toml',
        'pattern': re.compile(r'version = "(v\d+\.\d+\.\d+)"'),
        'template': 'version = "{version}"',
    })
```

## Automation and Scripting

### Automated Release Scripts

```bash
#!/bin/bash
# automated-release.sh

set -e  # Exit on any error

# Configuration
REPO_URL="https://github.com/user/repo"
BRANCH="main"

# Functions
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

check_clean_working_directory() {
    if ! python grtp.py --view | grep -q "Working directory clean"; then
        log "ERROR: Working directory not clean"
        python grtp.py --view
        exit 1
    fi
}

determine_version_increment() {
    local last_tag=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
    local commits=$(git log --oneline ${last_tag}..HEAD)
    
    if echo "$commits" | grep -q "BREAKING CHANGE\|!:"; then
        echo "major"
    elif echo "$commits" | grep -q "^feat"; then
        echo "minor"
    else
        echo "patch"
    fi
}

# Main workflow
main() {
    log "Starting automated release process"
    
    # Pre-flight checks
    log "Checking working directory status"
    check_clean_working_directory
    
    # Determine version increment
    INCREMENT=$(determine_version_increment)
    log "Determined version increment: $INCREMENT"
    
    # Show preview
    log "Preview of changes:"
    python grtp.py --view --${INCREMENT}
    
    # Confirm release
    read -p "Proceed with $INCREMENT release? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "Release cancelled"
        exit 0
    fi
    
    # Execute release
    log "Incrementing version ($INCREMENT)"
    python grtp.py --${INCREMENT}
    
    log "Preparing release documentation"
    python grtp.py --release-prepare
    
    log "Creating git tag"
    python grtp.py --release-deploy -m "Automated $INCREMENT release"
    
    log "Pushing changes"
    git push origin $BRANCH
    git push origin --tags
    
    log "Release completed successfully"
}

# Run main function
main "$@"
```

### CI/CD Integration

#### GitHub Actions

```yaml
# .github/workflows/release.yml
name: Automated Release

on:
  push:
    branches: [ main ]
  workflow_dispatch:
    inputs:
      increment:
        description: 'Version increment type'
        required: true
        default: 'patch'
        type: choice
        options:
        - patch
        - minor
        - major

jobs:
  release:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
      with:
        fetch-depth: 0  # Full history for git operations
        
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
        
    - name: Check working directory
      run: |
        python grtp.py --view
        
    - name: Determine increment type
      id: increment
      run: |
        if [ "${{ github.event_name }}" = "workflow_dispatch" ]; then
          echo "type=${{ github.event.inputs.increment }}" >> $GITHUB_OUTPUT
        else
          # Auto-determine from commits
          if git log --oneline $(git describe --tags --abbrev=0)..HEAD | grep -q "BREAKING CHANGE"; then
            echo "type=major" >> $GITHUB_OUTPUT
          elif git log --oneline $(git describe --tags --abbrev=0)..HEAD | grep -q "^feat"; then
            echo "type=minor" >> $GITHUB_OUTPUT
          else
            echo "type=patch" >> $GITHUB_OUTPUT
          fi
        fi
        
    - name: Increment version
      run: |
        python grtp.py --${{ steps.increment.outputs.type }}
        
    - name: Prepare release
      run: |
        python grtp.py --release-prepare
        
    - name: Get new version
      id: version
      run: |
        VERSION=$(python grtp.py --view | grep "Highest version:" | cut -d' ' -f3)
        echo "version=$VERSION" >> $GITHUB_OUTPUT
        
    - name: Create git tag
      run: |
        python grtp.py --release-deploy -m "Release ${{ steps.version.outputs.version }}"
        
    - name: Push changes
      run: |
        git push origin main
        git push origin --tags
        
    - name: Create GitHub Release
      uses: actions/create-release@v1
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      with:
        tag_name: ${{ steps.version.outputs.version }}
        release_name: Release ${{ steps.version.outputs.version }}
        body_path: RELEASES.md
        draft: false
        prerelease: false
```

## Integration with External Tools

### Package Manager Integration

#### Python (setup.py)

```python
# setup.py with dynamic version reading
import re
import os

def get_version():
    """Extract version from grtp managed files"""
    version_file = os.path.join(os.path.dirname(__file__), 'src', '__init__.py')
    with open(version_file, 'r') as f:
        content = f.read()
    
    match = re.search(r'__version__ = "(v\d+\.\d+\.\d+)"', content)
    if match:
        return match.group(1)
    
    raise RuntimeError("Unable to find version string")

setup(
    name="my-package",
    version=get_version(),
    # ... other setup parameters
)
```

#### Node.js (package.json)

```javascript
// scripts/sync-version.js
const fs = require('fs');
const { execSync } = require('child_process');

// Get version from grtp
const output = execSync('python grtp.py --view', { encoding: 'utf8' });
const versionMatch = output.match(/Highest version: (v\d+\.\d+\.\d+)/);

if (versionMatch) {
    const version = versionMatch[1];
    
    // Update package.json
    const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
    packageJson.version = version;
    fs.writeFileSync('package.json', JSON.stringify(packageJson, null, 2));
    
    console.log(`Updated package.json to version ${version}`);
}
```

### Documentation Integration

#### Sphinx Documentation

```python
# docs/conf.py
import sys
import os
import re

# Add project root to path
sys.path.insert(0, os.path.abspath('..'))

def get_version():
    """Get version from grtp managed files"""
    version_file = os.path.join(os.path.dirname(__file__), '..', 'src', '__init__.py')
    with open(version_file, 'r') as f:
        content = f.read()
    
    match = re.search(r'__version__ = "(v\d+\.\d+\.\d+)"', content)
    if match:
        return match.group(1)
    
    return "unknown"

# Project information
project = 'My Project'
version = get_version()
release = version
```

#### MkDocs Integration

```yaml
# mkdocs.yml
site_name: My Project
site_description: Project documentation

# Use version from grtp
site_version: !ENV [PROJECT_VERSION, 'development']

# In CI/CD, set PROJECT_VERSION environment variable:
# export PROJECT_VERSION=$(python grtp.py --view | grep "Highest version:" | cut -d' ' -f3)
```