# 🔧 Troubleshooting Guide

## Common Issues

### "No versions found in configured files"

**Cause**: The regex patterns don't match the version format in your files.

**Solutions**:
1. Check that your version format matches the regex pattern (e.g., `v1.2.3` vs `1.2.3`)
2. Verify the regex pattern has a capture group: `(v\d+\.\d+\.\d+)`
3. Test your regex pattern with a regex tester
4. Use `--view` to see which files are being scanned

**Example**:
```bash
# Check what files are being scanned
python v-and-r.py --view

# Test your regex pattern
python -c "import re; print(re.compile(r'version = \"(v\d+\.\d+\.\d+)\"').search('version = \"v1.2.3\"'))"
```

### "Pattern must have at least one capture group"

**Cause**: The regex pattern doesn't include parentheses around the version.

**Solution**: Add parentheses around the version part:
```python
# Wrong
'pattern': re.compile(r'version = "v\d+\.\d+\.\d+"')

# Correct
'pattern': re.compile(r'version = "(v\d+\.\d+\.\d+)"')
```

### "Template must contain {version} placeholder"

**Cause**: The template string is missing the `{version}` placeholder.

**Solution**: Include `{version}` in your template:
```python
# Wrong
'template': 'version = "1.0.0"'

# Correct
'template': 'version = "{version}"'
```

### "No files match the pattern"

**Cause**: The file glob pattern doesn't match any existing files.

**Solutions**:
1. Check file paths are correct relative to where you run the script
2. Verify glob patterns: `*.py` (current directory), `src/*.py` (src directory)
3. Use absolute paths if needed
4. Check file permissions

**Debugging**:
```bash
# Test glob patterns manually
ls -la *.py
ls -la src/*.py

# Check current directory
pwd
ls -la
```

### "Git command failed" or "Not in a git repository"

**Cause**: Git is not available or the current directory is not a git repository.

**Solutions**:
1. Initialize git repository: `git init`
2. Install git if not available
3. Run the command from within a git repository
4. Some features work without git (version management still functions)

**Verification**:
```bash
# Check if git is available
git --version

# Check if in git repository
git status

# Initialize git repository if needed
git init
```

### "Cannot write to file"

**Cause**: File permissions or file is locked by another process.

**Solutions**:
1. Check file permissions: `chmod 644 filename`
2. Ensure files are not open in editors
3. Run with appropriate permissions
4. Check disk space

**Debugging**:
```bash
# Check file permissions
ls -la README.md

# Check disk space
df -h

# Test write permissions
touch test-write && rm test-write
```

## Debugging Tips

### 1. Use `--view` first
Always check what versions are detected before making changes:
```bash
python v-and-r.py --view
```

### 2. Enable debug mode
Use debug logging for detailed information:
```bash
python v-and-r.py --debug --view
```

### 3. Test regex patterns
Use online regex testers or Python to verify patterns:
```python
import re
pattern = re.compile(r'version = "(v\d+\.\d+\.\d+)"')
text = 'version = "v1.2.3"'
match = pattern.search(text)
print(match.group(1) if match else "No match")
```

### 4. Check file paths
Ensure glob patterns match your project structure:
```bash
# Test glob patterns
python -c "import glob; print(glob.glob('src/*.py'))"
```

### 5. Validate configuration
Check configuration syntax:
```python
# Test configuration entry
config = {
    'file': 'README.md',
    'pattern': re.compile(r'- Version (v\d+\.\d+\.\d+)'),
    'template': '- Version {version}',
}
```

## Validation Errors

### Configuration Validation

The tool validates configuration on startup:

```bash
# Error: Empty configuration
Error in VERSION_FILES configuration: VERSION_FILES configuration cannot be empty

# Error: Missing required keys
Error in VERSION_FILES configuration: Configuration entry 0 missing required key: 'pattern'

# Error: Invalid regex
Error in VERSION_FILES configuration: Configuration entry 0: 'pattern' must be a compiled regex

# Error: No capture groups
Error in VERSION_FILES configuration: Configuration entry 0: regex pattern must have at least one capture group

# Error: Missing placeholder
Error in VERSION_FILES configuration: Configuration entry 0: template must contain '{version}' placeholder
```

### Runtime Validation

```bash
# Error: Multiple increment types
Error: Only one increment type (-p, -mi, -ma) can be specified at a time

# Error: Invalid message usage
Error: -m/--message option can only be used with --release-deploy

# Error: Invalid release-diff arguments
Error: --release-diff accepts 1 or 2 tags only
```

## Performance Issues

### Large Repositories

**Problem**: Slow performance with large git repositories.

**Solutions**:
1. Use specific patterns instead of `**/*` wildcards
2. Limit git history analysis
3. Use `--view` instead of full release preparation for quick checks

### Many Files

**Problem**: Slow file processing with many configured files.

**Solutions**:
1. Split configuration for different file types
2. Use more specific glob patterns
3. Process files in batches

### Network Drives

**Problem**: Slow file operations on network storage.

**Solutions**:
1. Work on local copies when possible
2. Use faster network connections
3. Cache results when appropriate

## Recovery Procedures

### Rollback Failed Version Increment

```bash
# Check git status
git status

# Restore files from git
git checkout -- .

# Or restore specific files
git checkout -- README.md src/app.py

# Verify restoration
python v-and-r.py --view
```

### Fix Version Inconsistencies

```bash
# Find all versions
python v-and-r.py --view

# Manually fix files with wrong versions
# Edit files to match the highest version

# Verify consistency
python v-and-r.py --view

# If needed, force update to specific version
# (Edit VERSION_FILES to temporarily match current versions, then increment)
```

### Recover from Git Issues

```bash
# If git tags are corrupted
git tag -d v1.2.3  # Delete bad tag
python v-and-r.py --release-deploy -m "Recreate v1.2.3"

# If git history is problematic
git log --oneline  # Check history
git reflog  # Check reference log

# Reset to known good state if needed
git reset --hard HEAD~1
```

## Error Messages Reference

### Exit Codes
- **0**: Success
- **1**: General error
- **2**: Configuration error  
- **3**: Version error
- **4**: File error
- **5**: Git error

### Common Error Patterns

```bash
# Configuration errors (exit code 2)
"VERSION_FILES configuration cannot be empty"
"Missing required configuration key"
"Pattern must be a compiled regex object"

# Version errors (exit code 3)
"Invalid version format"
"Cannot compare versions"
"No valid versions found"

# File errors (exit code 4)
"Cannot read file"
"Cannot write file"
"No configuration found for file"

# Git errors (exit code 5)
"Not in a git repository"
"Git command failed"
"Tag does not exist"
```

## Getting Help

### Built-in Help

```bash
# General help
python v-and-r.py --help

# Command-specific examples
python v-and-r.py --help | grep -A5 "Examples:"
```

### Debug Information

```bash
# Enable debug logging
python v-and-r.py --debug --view

# Check Python version
python --version

# Check git version
git --version
```

### Community Support

1. Check existing issues in the repository
2. Create detailed bug reports with:
   - Command used
   - Error message
   - Configuration (sanitized)
   - Environment details (OS, Python version, git version)
3. Include minimal reproduction case

### Self-Diagnosis Checklist

Before reporting issues:

- [ ] Verified Python 3.6+ is installed
- [ ] Confirmed git is available (if using git features)
- [ ] Tested with `--view` command first
- [ ] Checked file permissions
- [ ] Validated regex patterns
- [ ] Reviewed configuration syntax
- [ ] Tried with debug mode enabled
- [ ] Tested in a clean directory