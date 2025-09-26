# 🤝 Contributing Guide

## Welcome Contributors!

Thank you for your interest in contributing to v-and-r! This guide will help you get started with contributing to the project.

## Getting Started

### Prerequisites

- Python 3.6 or higher
- Git
- Basic understanding of semantic versioning
- Familiarity with command-line tools

### Development Setup

1. **Fork and Clone**
   ```bash
   # Fork the repository on GitHub, then clone your fork
   git clone https://github.com/YOUR-USERNAME/v-and-r.git
   cd v-and-r
   
   # Add upstream remote
   git remote add upstream https://github.com/ORIGINAL-OWNER/v-and-r.git
   ```

2. **Set up Development Environment**
   ```bash
   # Create a virtual environment (optional but recommended)
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install development dependencies (if any)
   # Currently, v-and-r uses only standard library modules
   
   # Make the script executable
   chmod +x v-and-r.py
   ```

3. **Verify Setup**
   ```bash
   # Test the tool
   python v-and-r.py --help
   python v-and-r.py --test  # Run built-in tests
   ```

## Development Workflow

### Branch Strategy

- **main**: Stable release branch
- **develop**: Development branch for new features
- **feature/**: Feature branches (e.g., `feature/add-dry-run`)
- **bugfix/**: Bug fix branches (e.g., `bugfix/fix-regex-pattern`)
- **hotfix/**: Critical fixes for production

### Making Changes

1. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Your Changes**
   - Follow the existing code style
   - Add tests for new functionality
   - Update documentation as needed

3. **Test Your Changes**
   ```bash
   # Run built-in tests
   python v-and-r.py --test
   
   # Test manually with different scenarios
   python v-and-r.py --view
   python v-and-r.py --patch
   ```

4. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

### Commit Message Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

Examples:
```bash
git commit -m "feat: add --dry-run flag for testing changes"
git commit -m "fix: resolve regex pattern matching issue"
git commit -m "docs: update configuration examples"
```

## Code Guidelines

### Code Style

- **PEP 8**: Follow Python PEP 8 style guidelines
- **Type Hints**: Use type hints for function parameters and return values
- **Docstrings**: Include docstrings for all classes and functions
- **Comments**: Add comments for complex logic

### Example Code Style

```python
def increment_version(version: str, increment_type: str) -> str:
    """
    Increment version number based on semantic versioning.
    
    Args:
        version: Current version string (e.g., 'v1.2.3')
        increment_type: Type of increment ('patch', 'minor', 'major')
        
    Returns:
        New version string
        
    Raises:
        VersionError: If version format is invalid
    """
    # Parse version components
    major, minor, patch = parse_version(version)
    
    # Increment based on type
    if increment_type == 'patch':
        patch += 1
    elif increment_type == 'minor':
        minor += 1
        patch = 0
    elif increment_type == 'major':
        major += 1
        minor = 0
        patch = 0
    else:
        raise ValueError(f"Invalid increment type: {increment_type}")
    
    return f"v{major}.{minor}.{patch}"
```

### Testing Guidelines

1. **Add Tests for New Features**
   ```python
   def test_new_feature():
       """Test new feature functionality"""
       # Arrange
       input_data = "test input"
       expected_output = "expected result"
       
       # Act
       result = new_feature_function(input_data)
       
       # Assert
       assert result == expected_output
   ```

2. **Test Edge Cases**
   - Invalid inputs
   - Empty files
   - Missing git repository
   - Permission errors

3. **Integration Tests**
   - Test complete workflows
   - Test with real git repositories
   - Test with various file formats

### Documentation Guidelines

1. **Update README.md** for user-facing changes
2. **Add/Update docs/** for detailed documentation
3. **Include examples** in documentation
4. **Update help text** in the script

## Types of Contributions

### Bug Reports

When reporting bugs, please include:

1. **Clear Description**: What you expected vs. what happened
2. **Steps to Reproduce**: Minimal steps to reproduce the issue
3. **Environment**: OS, Python version, git version
4. **Configuration**: Relevant VERSION_FILES configuration (sanitized)
5. **Error Messages**: Complete error messages and stack traces

**Bug Report Template:**
```markdown
## Bug Description
Brief description of the bug

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
What you expected to happen

## Actual Behavior
What actually happened

## Environment
- OS: [e.g., Ubuntu 20.04, macOS 12.0, Windows 10]
- Python Version: [e.g., 3.9.7]
- Git Version: [e.g., 2.34.1]

## Configuration
```python
VERSION_FILES = [
    # Your configuration here (remove sensitive data)
]
```

## Error Messages
```
Paste complete error messages here
```
```

### Feature Requests

For feature requests, please include:

1. **Use Case**: Why is this feature needed?
2. **Proposed Solution**: How should it work?
3. **Alternatives**: Other ways to achieve the same goal
4. **Examples**: Usage examples of the proposed feature

### Code Contributions

#### Priority Areas

1. **Core Functionality**
   - Version parsing and validation
   - File pattern matching
   - Git integration improvements

2. **User Experience**
   - Better error messages
   - Improved output formatting
   - Progress indicators

3. **Configuration**
   - External configuration files
   - Configuration validation
   - Template improvements

4. **Testing**
   - Increase test coverage
   - Integration tests
   - Performance tests

#### Feature Ideas

- [ ] `--dry-run` flag for testing changes
- [ ] External configuration files (.v-and-r.json)
- [ ] Plugin system for custom strategies
- [ ] Web interface for release management
- [ ] Support for pre-release versions
- [ ] Monorepo support
- [ ] CI/CD integration helpers

### Documentation Contributions

- Improve existing documentation
- Add more examples
- Create tutorials
- Translate documentation
- Fix typos and grammar

## Pull Request Process

### Before Submitting

1. **Sync with Upstream**
   ```bash
   git fetch upstream
   git checkout main
   git merge upstream/main
   git checkout your-feature-branch
   git rebase main
   ```

2. **Run Tests**
   ```bash
   python v-and-r.py --test
   ```

3. **Update Documentation**
   - Update relevant documentation files
   - Add examples for new features
   - Update help text if needed

### Submitting Pull Request

1. **Push Your Branch**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create Pull Request**
   - Use descriptive title
   - Fill out the PR template
   - Link related issues
   - Add screenshots if applicable

3. **PR Template**
   ```markdown
   ## Description
   Brief description of changes
   
   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Documentation update
   - [ ] Refactoring
   
   ## Testing
   - [ ] Tests pass
   - [ ] Manual testing completed
   - [ ] Documentation updated
   
   ## Related Issues
   Closes #123
   
   ## Screenshots (if applicable)
   ```

### Review Process

1. **Automated Checks**: CI/CD will run tests
2. **Code Review**: Maintainers will review your code
3. **Feedback**: Address any requested changes
4. **Approval**: Once approved, your PR will be merged

## Development Tips

### Testing Locally

```bash
# Test with different configurations
mkdir test-project
cd test-project

# Create test files
echo '# Test Project\n- Version v1.0.0' > README.md
echo 'version = "v1.0.0"' > app.py

# Test v-and-r
python ../v-and-r.py --view
python ../v-and-r.py --patch
```

### Debugging

```bash
# Enable debug mode
python v-and-r.py --debug --view

# Test specific components
python -c "
import sys
sys.path.append('.')
from v_and_r import VersionManager
vm = VersionManager()
print(vm.parse_version('v1.2.3'))
"
```

### Performance Testing

```bash
# Test with large repositories
git clone https://github.com/large-repo/example.git
cd example
python ../v-and-r.py --view

# Time operations
time python v-and-r.py --release-last
```

## Community Guidelines

### Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Help others learn and grow

### Communication

- **GitHub Issues**: Bug reports and feature requests
- **Pull Requests**: Code contributions and discussions
- **Discussions**: General questions and ideas

### Getting Help

1. **Check Documentation**: Read the docs first
2. **Search Issues**: Look for existing solutions
3. **Ask Questions**: Create a discussion or issue
4. **Be Patient**: Maintainers are volunteers

## Release Process

### For Maintainers

1. **Version Increment**
   ```bash
   python v-and-r.py --minor  # or --patch, --major
   ```

2. **Update Documentation**
   ```bash
   python v-and-r.py --release-prepare
   ```

3. **Create Release**
   ```bash
   python v-and-r.py --release-deploy -m "Release v1.2.0"
   ```

4. **Publish**
   ```bash
   git push origin main --tags
   ```

### Release Schedule

- **Patch releases**: As needed for bug fixes
- **Minor releases**: Monthly for new features
- **Major releases**: Quarterly for breaking changes

## Recognition

Contributors will be recognized in:

- CHANGELOG.md for each release
- README.md contributors section
- Release notes
- Special thanks in major releases

Thank you for contributing to v-and-r! 🚀