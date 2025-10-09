# v-and-r (Version and Release Manager)

- Version v1.2.4

A command-line tool that automates version management and release processes across multiple project files. The tool follows semantic versioning principles, integrates with git for release management, and ensures version consistency across all configured files in a project.


## Usage
```
v-and-r view (default) --git 
v-and-r patch 
v-and-r minor
v-and-r major
v-and-r release-prepare
v-and-r release-deploy

```

## 🚀 Quick Start

```bash
# Download and setup
curl -O https://raw.githubusercontent.com/your-repo/v-and-r.py
chmod +x v-and-r.py

# View current project status (comprehensive overview)
python v-and-r.py

# Increment versions
python v-and-r.py --patch    # Bug fixes (v1.2.3 → v1.2.4)
python v-and-r.py --minor    # New features (v1.2.3 → v1.3.0)  
python v-and-r.py --major    # Breaking changes (v1.2.3 → v2.0.0)

# Release management
python v-and-r.py --release-prepare    # Update docs
python v-and-r.py --release-deploy     # Create git tag
```

## ✨ Key Features

- **🔍 Smart Version Discovery**: Automatically finds versions across multiple files
- **📊 Comprehensive Overview**: Shows versions, git history, and working directory status
- **🎯 Semantic Versioning**: Patch, minor, and major increments with preview
- **📝 Release Management**: Automated CHANGELOG.md, RELEASES.md, and version.json generation
- **🔗 Git Integration**: Tag management, commit analysis, and release notes
- **⚙️ Flexible Configuration**: Regex patterns and glob support for any project structure

## 📖 Documentation

For detailed information, see our comprehensive documentation:

- **[📚 Documentation Hub](docs/README.md)** - Complete documentation overview
- **[📥 Installation Guide](docs/installation.md)** - Setup and requirements
- **[⚙️ Configuration Guide](docs/configuration.md)** - File patterns and examples  
- **[💡 Usage Examples](docs/usage-examples.md)** - Common workflows and scenarios
- **[📚 Command Reference](docs/command-reference.md)** - Complete CLI documentation
- **[🔧 Troubleshooting](docs/troubleshooting.md)** - Common issues and solutions
- **[🤝 Contributing](docs/contributing.md)** - Development and contribution guide
- **[🗺️ Roadmap](docs/ROADMAP.md)** - Future features and development plans

## 🎯 Common Commands

| Command | Description | Example |
|---------|-------------|---------|
| `python v-and-r.py` | View project status (default) | Shows versions, git info, working directory |
| `python v-and-r.py -p` | Increment patch version | v1.2.3 → v1.2.4 |
| `python v-and-r.py -v -mi` | Preview next minor version | Shows what v1.3.0 would be |
| `python v-and-r.py --release-diff v1.0.0` | Show commits since tag | All changes since v1.0.0 |
| `python v-and-r.py --release-prepare` | Prepare release docs | Updates CHANGELOG.md, RELEASES.md |

## ⚡ What You Get

### Comprehensive Project Overview
```bash
$ python v-and-r.py
v-and-r (Version and Release Manager)
==================================================
Current versions across configured files:
  README.md: v1.2.3
  src/app.py: v1.2.3
  package.json: v1.2.3

Highest version: v1.2.3
Next patch version: v1.2.4

==================================================
Git Information:
Last tag: v1.2.0
Commits since v1.2.0 (5 commits):
abc1234  feat: add user authentication
def5678  fix: resolve memory leak
...

Working Directory Status:
Changes not staged for commit:
  modified:   src/app.py
Untracked files:
  new-feature.py
Summary: 1 changed file, 1 untracked file
```

### Automated Release Documentation
- **version.json**: Machine-readable release metadata
- **CHANGELOG.md**: Human-readable change history  
- **RELEASES.md**: Release summaries and highlights

## 🔧 Configuration

### External Configuration (Recommended)

Create a `.v-and-r.json` configuration file in your project root:

```bash
v-and-r --init  # Creates default .v-and-r.json
```

Edit the generated `.v-and-r.json` file:

```json
{
  "VERSION_FILES": [
    {
      "file": "README.md",
      "pattern": "- Version v(\\d+\\.\\d+\\.\\d+)",
      "template": "- Version v{version}"
    },
    {
      "file": "*.py",
      "pattern": "version = \"v(\\d+\\.\\d+\\.\\d+)\"",
      "template": "version = \"v{version}\""
    }
  ]
}
```

### Embedded Configuration (Fallback)

If no `.v-and-r.json` file exists, the tool uses embedded configuration in `v-and-r.py`. This provides backward compatibility but external configuration is recommended for easier maintenance.

See [Configuration Guide](docs/configuration.md) for detailed examples and patterns.

## 🚦 Quick Troubleshooting

**No versions found?** Check your regex patterns have capture groups: `(v\d+\.\d+\.\d+)`

**Files not updating?** Verify file paths and permissions with `python v-and-r.py --view`

**Git errors?** Ensure you're in a git repository: `git init` if needed

See [Troubleshooting Guide](docs/troubleshooting.md) for complete solutions.

## 🤝 Contributing

We welcome contributions! See our [Contributing Guide](docs/contributing.md) for:
- Development setup
- Code guidelines  
- Feature requests
- Bug reports

## 🐛 Known bugs
- [x] ~~version should be only 3 integers separated by dots, the prefixed v should resolved in config VERSION_FILES~~ **FIXED**


## 📋 Roadmap

- [x] Enhanced view with git status and next version preview
- [x] Git tag deployment with custom messages  
- [x] Comprehensive documentation organization
- [ ] `--dry-run` mode for safe testing
- [ ] External configuration files support
- [ ] Pre-release version support

See [Roadmap](docs/ROADMAP.md) for complete feature plans.

## 📄 License

MIT License - see LICENSE file for details.

---

**Need help?** Check the [documentation](docs/) or create an issue for support!