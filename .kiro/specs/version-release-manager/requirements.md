# Requirements Document

## Introduction

The v-and-r (Version and Release Manager) is a command-line tool that automates version management and release processes across multiple project files. The tool follows semantic versioning principles, integrates with git for release management, and ensures version consistency across all configured files in a project. It provides a single interface for version discovery, incrementation, and release documentation generation.

all configured files are defined in VERSION_FILES 

## Requirements

### Requirement 1

**User Story:** As a developer, I want to view current versions across all configured files, so that I can understand the current state of my project's versioning.

#### Acceptance Criteria

1. WHEN the user runs `v-and-r -v` or `v-and-r --view` THEN the system SHALL display the current version found in each configured file
2. WHEN multiple files contain different versions THEN the system SHALL display all versions and highlight the highest version
3. WHEN no version is found in a file THEN the system SHALL indicate that no version was detected for that file
4. WHEN the command is run without arguments THEN the system SHALL default to the view behavior

### Requirement 2

**User Story:** As a developer, I want to increment patch versions across all files, so that I can release bug fixes with consistent versioning.

#### Acceptance Criteria

1. WHEN the user runs `v-and-r -p` or `v-and-r --patch` THEN the system SHALL find the highest version across all files
2. WHEN the highest version is identified THEN the system SHALL increment the patch number (e.g., v1.2.3 becomes v1.2.4)
3. WHEN the new version is calculated THEN the system SHALL update all configured files with the new version
4. WHEN files are updated THEN the system SHALL preserve the original format and only replace the version number

### Requirement 3

**User Story:** As a developer, I want to increment minor versions across all files, so that I can release new features with consistent versioning.

#### Acceptance Criteria

1. WHEN the user runs `v-and-r -mi` or `v-and-r --minor` THEN the system SHALL find the highest version across all files
2. WHEN the highest version is identified THEN the system SHALL increment the minor number and reset patch to 0 (e.g., v1.2.3 becomes v1.3.0)
3. WHEN the new version is calculated THEN the system SHALL update all configured files with the new version

### Requirement 4

**User Story:** As a developer, I want to increment major versions across all files, so that I can release breaking changes with consistent versioning.

#### Acceptance Criteria

1. WHEN the user runs `v-and-r -ma` or `v-and-r --major` THEN the system SHALL find the highest version across all files
2. WHEN the highest version is identified THEN the system SHALL increment the major number and reset minor and patch to 0 (e.g., v1.2.3 becomes v2.0.0)
3. WHEN the new version is calculated THEN the system SHALL update all configured files with the new version

### Requirement 5

**User Story:** As a developer, I want to generate release information and metadata, so that I can document releases and track version history.

#### Acceptance Criteria

1. WHEN the user runs `v-and-r -r` or `v-and-r --release-info` THEN the system SHALL generate a version.json file with release metadata
2. WHEN version.json is generated THEN it SHALL contain the current version, timestamp, and commit information
3. WHEN the command is executed THEN the system SHALL display release notes based on git commit history
4. WHEN git tags exist THEN the system SHALL use tag information to generate release notes

### Requirement 6

**User Story:** As a developer, I want to compare commits between specific git tags, so that I can understand changes between releases.

#### Acceptance Criteria

1. WHEN the user runs `v-and-r -rd tag1 tag2` or `v-and-r --release-diff tag1 tag2` THEN the system SHALL show commits only between the specified tags
2. WHEN invalid tags are provided THEN the system SHALL display an error message
3. WHEN the tags are valid THEN the system SHALL format the commit list in a readable format

### Requirement 7

**User Story:** As a developer, I want to see commits since the last release, so that I can understand what changes will be included in the next release.

#### Acceptance Criteria

1. WHEN the user runs `v-and-r -rl` or `v-and-r --release-last` THEN the system SHALL show commits from the last git tag to HEAD
2. WHEN no git tags exist THEN the system SHALL show all commits from the beginning
3. WHEN displaying commits THEN the system SHALL NOT update version.json file

### Requirement 8

**User Story:** As a developer, I want to prepare comprehensive release documentation, so that I can maintain proper release records.

#### Acceptance Criteria

1. WHEN the user runs `v-and-r -rp` or `v-and-r --release-prepare` THEN the system SHALL update the version.json file
2. WHEN preparing a release THEN the system SHALL create or update CHANGELOG.md file
3. WHEN preparing a release THEN the system SHALL create or update RELEASES.md file
4. WHEN updating documentation files THEN the system SHALL preserve existing content and append new release information

### Requirement 9

**User Story:** As a developer, I want to configure which files and patterns to update, so that I can customize the tool for my project structure.

#### Acceptance Criteria

1. WHEN the tool is configured THEN it SHALL use a VERSION_FILES array to define file patterns
2. WHEN a file configuration is defined THEN it SHALL include file path (supporting wildcards), regex pattern, and template format
3. WHEN wildcards are used in file paths THEN the system SHALL expand them to match actual files (e.g., *.py, directory/*.py)
4. WHEN regex patterns are defined THEN the version SHALL be captured in the first capture group
5. WHEN templates are defined THEN they SHALL use {version} placeholder for version replacement

### Requirement 10

**User Story:** As a developer, I want to see help information, so that I can understand how to use all available commands.

#### Acceptance Criteria

1. WHEN the user runs `v-and-r -h` or `v-and-r --help` THEN the system SHALL display comprehensive help information
2. WHEN help is displayed THEN it SHALL include all available commands with their descriptions
3. WHEN help is displayed THEN it SHALL include usage examples and configuration guidance

### Requirement 11

**User Story:** As a developer, I want the tool to follow semantic versioning principles, so that version numbers are meaningful and consistent.

#### Acceptance Criteria

1. WHEN versions are processed THEN they SHALL follow the format vMAJOR.MINOR.PATCH
2. WHEN versions are compared THEN the system SHALL correctly identify the highest semantic version
3. WHEN versions are incremented THEN the system SHALL follow semantic versioning rules for major, minor, and patch increments

### Requirement 12

**User Story:** As a developer, I want git integration for release management, so that I can leverage existing version control information.

#### Acceptance Criteria

1. WHEN git operations are performed THEN the system SHALL integrate with the local git repository
2. WHEN git tags are used THEN the system SHALL correctly parse and compare tag versions
3. WHEN git commits are analyzed THEN the system SHALL provide meaningful commit history information
4. WHEN git is not available THEN the system SHALL gracefully handle the absence of git integration