# 📥 Installation Guide

## Quick Installation

Simply download the `v-and-r.py` script and make it executable:

```bash
# Download the script
curl -O https://raw.githubusercontent.com/your-repo/v-and-r.py

# Make it executable
chmod +x v-and-r.py

# Optionally, create a symlink for easier access
ln -s $(pwd)/v-and-r.py /usr/local/bin/v-and-r
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
wget https://raw.githubusercontent.com/your-repo/v-and-r/main/v-and-r.py

# Or using curl
curl -O https://raw.githubusercontent.com/your-repo/v-and-r/main/v-and-r.py

# Make executable
chmod +x v-and-r.py
```

### Method 2: Git Clone

```bash
# Clone the repository
git clone https://github.com/your-repo/v-and-r.git
cd v-and-r

# Make executable
chmod +x v-and-r.py

# Optional: Create system-wide symlink
sudo ln -s $(pwd)/v-and-r.py /usr/local/bin/v-and-r
```

### Method 3: Package Manager (Future)

```bash
# Coming soon
pip install v-and-r
# or
brew install v-and-r
```

## Quick Start

After installation, verify the tool works:

```bash
# Check help
python v-and-r.py --help

# View current project status (if in a project directory)
python v-and-r.py --view
```

## System Integration

### Creating a System Command

To use `v-and-r` as a system command:

```bash
# Create symlink in PATH
sudo ln -s $(pwd)/v-and-r.py /usr/local/bin/v-and-r

# Now you can use it anywhere
v-and-r --help
```

### Shell Alias

Add to your shell configuration (`.bashrc`, `.zshrc`, etc.):

```bash
alias v-and-r='python /path/to/v-and-r.py'
```

### Windows Installation

```cmd
# Download using PowerShell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/your-repo/v-and-r/main/v-and-r.py" -OutFile "v-and-r.py"

# Run with Python
python v-and-r.py --help
```

## Verification

Test your installation:

```bash
# Check version and help
python v-and-r.py --help

# Test in a sample directory
mkdir test-project
cd test-project
echo '# Test Project\n- Version v1.0.0' > README.md
python v-and-r.py --view
```

You should see output showing the detected version in README.md.

## Next Steps

1. **Configure your project**: See [Configuration Guide](configuration.md)
2. **Learn basic usage**: See [Usage Examples](usage-examples.md)
3. **Explore commands**: See [Command Reference](command-reference.md)