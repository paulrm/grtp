# Project Structure

## Root Directory Layout
```
/
├── README.md              # Project documentation and usage examples
├── grtp.py               # Main CLI script (to be created)
├── .kiro/                # Kiro AI assistant configuration
│   ├── specs/            # Feature specifications
│   └── steering/         # AI guidance documents
└── version.json          # Generated release metadata (created by tool)
```

## Core Files
- **grtp.py**: Main executable script containing all CLI functionality
- **README.md**: Contains usage documentation and VERSION_FILES configuration examples
- **version.json**: Auto-generated file containing release metadata and version history

## Configuration Approach
- **Embedded Configuration**: VERSION_FILES array defined within the main script
- **Inline Documentation**: Configuration examples provided in README.md
- **No External Config Files**: Keeps the tool self-contained and portable

## Kiro Workspace Structure
- **.kiro/specs/**: Contains detailed requirements and design specifications
- **.kiro/steering/**: AI assistant guidance documents for consistent development
- **Specifications**: Follow structured format with requirements, acceptance criteria, and user stories

## File Naming Conventions
- **Script Name**: `grtp.py` (matches CLI command name)
- **Generated Files**: `version.json` for release metadata
- **Documentation**: Standard `README.md` for project documentation

## Development Workflow
1. Specifications defined in `.kiro/specs/`
2. Implementation in single `grtp.py` file
3. Configuration examples maintained in README.md
4. Testing using `--view` and `--dry-run` flags (when implemented)