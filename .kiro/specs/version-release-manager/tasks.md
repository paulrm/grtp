# Implementation Plan

- [x] 1. Set up project structure and core data models
  - Create the main v-and-r.py file with basic structure
  - Implement Version dataclass with comparison methods and string representation
  - Implement FileConfig dataclass for configuration entries
  - Implement ReleaseInfo dataclass for release metadata
  - Create custom exception classes (VAndRError, VersionError, FileError, GitError)
  - _Requirements: 11.1, 11.2, 9.1, 9.2_

- [x] 2. Implement VersionManager class with semantic versioning logic
  - Create VersionManager class with version parsing functionality
  - Implement parse_version method to extract major, minor, patch from version strings
  - Implement compare_versions method for semantic version comparison
  - Implement find_highest_version method to identify the highest version from a list
  - Implement increment_patch, increment_minor, and increment_major methods
  - Add comprehensive unit tests for all version operations
  - _Requirements: 11.1, 11.2, 11.3, 2.1, 2.2, 3.1, 3.2, 4.1, 4.2_

- [x] 3. Implement FileManager class for file operations and pattern matching
  - Create FileManager class with VERSION_FILES configuration support
  - Implement expand_file_patterns method to handle glob patterns like *.py and directory/*.py
  - Implement find_versions_in_files method to scan files and extract current versions using regex patterns
  - Implement update_file_version method to update a single file using its template
  - Implement update_all_files method to update versions across all configured files
  - Add validation for regex patterns and template formatting
  - Add comprehensive unit tests for file operations and pattern matching
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 1.1, 1.2, 1.3, 2.3, 2.4_

- [x] 4. Implement GitManager class for git integration
  - Create GitManager class with git repository detection
  - Implement is_git_repository method to check for git availability
  - Implement get_git_tags method to retrieve and sort git tags by version
  - Implement get_commits_between_tags method for commit history between specific tags
  - Implement get_commits_since_tag method for commits since last tag
  - Implement get_latest_tag method to find the most recent version tag
  - Add error handling for git command failures and non-git directories
  - Add unit tests with mocked git operations
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 6.1, 6.2, 7.1, 7.2_

- [x] 5. Implement CLI interface and argument parsing
  - Create CLIInterface class with argparse configuration
  - Implement parse_arguments method supporting all command-line options (-v, -p, -mi, -ma, -r, -rd, -rl, -rp, -h)
  - Add argument validation and error handling for invalid combinations
  - Implement help text generation with usage examples and descriptions
  - Add unit tests for argument parsing and validation
  - _Requirements: 10.1, 10.2, 10.3, 1.4_

- [x] 6. Implement view command functionality
  - Create view_versions method in CLIInterface to display current versions
  - Integrate FileManager to scan all configured files for versions
  - Implement version display formatting showing file paths and detected versions
  - Add logic to highlight the highest version when multiple versions exist
  - Handle cases where no versions are found in files
  - Add a sample dir and put files for testing
  - Add integration tests for view command with sample files
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 7. Implement version increment commands (patch, minor, major)
  - Create increment_version method in CLIInterface for version updates
  - Integrate VersionManager to find highest version and calculate new version
  - Integrate FileManager to update all configured files with new version
  - Implement rollback mechanism for failed file updates
  - Add confirmation and success/failure reporting
  - Add integration tests for all increment operations
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 4.1, 4.2, 4.3_

- [ ] 8. Implement release information generation
  - Create generate_release_info method to create version.json file
  - Integrate GitManager to gather commit history and tag information
  - Implement release notes formatting based on commit messages
  - Add timestamp and commit hash information to release metadata
  - Handle cases where git is not available with graceful degradation
  - Add integration tests for release info generation
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ] 9. Implement git diff and commit history commands
  - Create release_diff method to show commits between specific tags
  - Create release_last method to show commits since last tag
  - Implement commit formatting for readable output
  - Add validation for tag existence and git repository availability
  - Handle edge cases like no tags or invalid tag names
  - Add integration tests with mock git repositories
  - _Requirements: 6.1, 6.2, 6.3, 7.1, 7.2, 7.3_

- [ ] 10. Implement release preparation functionality
  - Create release_prepare method to update version.json, CHANGELOG.md, and RELEASES.md
  - Implement CHANGELOG.md creation and updating with new release information
  - Implement RELEASES.md creation and updating with release summaries
  - Add logic to preserve existing content while appending new information
  - Integrate with GitManager for commit history and version information
  - Add integration tests for release preparation workflow
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [ ] 11. Implement main execution flow and error handling
  - Create main function to orchestrate CLI parsing and command execution
  - Implement execute_command method to route to appropriate command handlers
  - Add comprehensive error handling with user-friendly error messages
  - Implement logging for debugging and troubleshooting
  - Add validation for VERSION_FILES configuration
  - Add integration tests for complete command workflows
  - _Requirements: 10.1, 12.4_

- [ ] 12. Add VERSION_FILES configuration and documentation
  - Define sample VERSION_FILES configuration array in the main script
  - Add configuration validation to ensure required fields are present
  - Create comprehensive documentation in README.md with usage examples
  - Add configuration examples for common file patterns and templates
  - Document all command-line options and their behaviors
  - Add troubleshooting guide for common issues
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 10.2, 10.3_