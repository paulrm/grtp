# 📥 Installation Guide

## Quick Installation

Simply download the `grtp.py` script and make it executable:

```bash
# Download the script
curl -O https://raw.githubusercontent.com/your-repo/grtp.py

# Make it executable
chmod +x grtp.py

# Optionally, create a symlink for easier access
ln -s $(pwd)/grtp.py /usr/local/bin/grtp
```

## Requirements

- **Python 3.6+**: The tool is written in Python and requires Python 3.6 or later
- **Git** (optional): For git integration features (tags, commit history, release management)

### Python Dependencies

The tool uses only Python standard library modules:
- `re` - Regular expressions for pattern matching
- `json` - JSON file generation
- `argparse` - Command-line argument parsing
- `subprocess` - Git command execution
- `glob` - File pattern matching
- `os`/`pathlib` - File system operations
- `datetime` - Timestamp generation
- `logging` - Debug and error logging

No external dependencies are required.

## Installation Methods

### Method 1: Direct Download

```bash
# Download directly
wget https://raw.githubusercontent.com/your-repo/grtp/main/grtp.py

# Or using curl
curl -O https://raw.githubusercontent.com/your-repo/grtp/main/grtp.py

# Make executable
chmod +x grtp.py
```

### Method 2: Git Clone

```bash
# Clone the repository
git clone https://github.com/your-repo/grtp.git
cd grtp

# Make executable
chmod +x grtp.py

# Optional: Create system-wide symlink
sudo ln -s $(pwd)/grtp.py /usr/local/bin/grtp
```

### Method 3: Package Manager (Future)

```bash
# Coming soon
pip install grtp
# or
brew install grtp
```

## Quick Start

After installation, verify the tool works:

```bash
# Check help
python grtp.py --help

# View current project status (if in a project directory)
python grtp.py --view
```

## System Integration

### Creating a System Command

To use `grtp` as a system command:

```bash
# Create symlink in PATH
sudo ln -s $(pwd)/grtp.py /usr/local/bin/grtp

# Now you can use it anywhere
grtp --help
```

### Shell Alias

Add to your shell configuration (`.bashrc`, `.zshrc`, etc.):

```bash
alias grtp='python /path/to/grtp.py'
```

### Windows Installation

```cmd
# Download using PowerShell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/your-repo/grtp/main/grtp.py" -OutFile "grtp.py"

# Run with Python
python grtp.py --help
```

## Verification

Test your installation:

```bash
# Check version and help
python grtp.py --help

# Test in a sample directory
mkdir test-project
cd test-project
echo '# Test Project\n- Version v1.0.0' > README.md
python grtp.py --view
```

You should see output showing the detected version in README.md.

## Next Steps

1. **Configure your project**: See [Configuration Guide](configuration.md)
2. **Learn basic usage**: See [Usage Examples](usage-examples.md)
3. **Explore commands**: See [Command Reference](command-reference.md)