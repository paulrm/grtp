#!/usr/bin/env python3
"""
v-and-r (Version and Release Manager)

A command-line tool that automates version management and release processes 
across multiple project files. Follows semantic versioning principles and 
integrates with git for release management.
"""

import re
import json
import argparse
import subprocess
import glob
import os
import sys
import datetime
import logging
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from pathlib import Path


# Custom Exception Classes
class VAndRError(Exception):
    """Base exception for v-and-r tool"""
    pass


class VersionError(VAndRError):
    """Version-related errors"""
    pass


class FileError(VAndRError):
    """File operation errors"""
    pass


class GitError(VAndRError):
    """Git integration errors"""
    pass


# Core Data Models
@dataclass
class Version:
    """Represents a semantic version with comparison capabilities"""
    major: int
    minor: int
    patch: int
    prefix: str = "v"
    
    def __str__(self) -> str:
        """String representation of version"""
        return f"{self.prefix}{self.major}.{self.minor}.{self.patch}"
    
    def __lt__(self, other: 'Version') -> bool:
        """Enable version comparison for sorting"""
        if self.major != other.major:
            return self.major < other.major
        if self.minor != other.minor:
            return self.minor < other.minor
        return self.patch < other.patch
    
    def __eq__(self, other: 'Version') -> bool:
        """Enable version equality comparison"""
        return (self.major == other.major and 
                self.minor == other.minor and 
                self.patch == other.patch)
    
    def __le__(self, other: 'Version') -> bool:
        """Enable less than or equal comparison"""
        return self < other or self == other
    
    def __gt__(self, other: 'Version') -> bool:
        """Enable greater than comparison"""
        return not self <= other
    
    def __ge__(self, other: 'Version') -> bool:
        """Enable greater than or equal comparison"""
        return not self < other


@dataclass
class FileConfig:
    """Represents a file configuration entry for version management"""
    file_pattern: str
    regex_pattern: re.Pattern
    template: str
    
    def matches_file(self, file_path: str) -> bool:
        """Check if file path matches this configuration pattern"""
        # Handle glob patterns
        if '*' in self.file_pattern:
            return any(Path(file_path).match(pattern) for pattern in glob.glob(self.file_pattern))
        return file_path == self.file_pattern


@dataclass
class ReleaseInfo:
    """Represents release metadata for version.json generation"""
    version: str
    timestamp: str
    commit_hash: str
    commits: List[Dict]
    previous_version: Optional[str] = None
    
    def to_json(self) -> str:
        """Convert release info to JSON format"""
        return json.dumps({
            'version': self.version,
            'timestamp': self.timestamp,
            'commit_hash': self.commit_hash,
            'previous_version': self.previous_version,
            'commits': self.commits
        }, indent=2)


# Core Manager Classes
class VersionManager:
    """Handles semantic version operations and comparisons"""
    
    def __init__(self):
        """Initialize VersionManager"""
        self.version_pattern = re.compile(r'^v?(\d+)\.(\d+)\.(\d+)$')
    
    def parse_version(self, version_string: str) -> Tuple[int, int, int]:
        """
        Parse version string into major, minor, patch components.
        
        Args:
            version_string: Version string like 'v1.2.3' or '1.2.3'
            
        Returns:
            Tuple of (major, minor, patch) as integers
            
        Raises:
            VersionError: If version string format is invalid
        """
        if not version_string:
            raise VersionError("Version string cannot be empty")
        
        match = self.version_pattern.match(version_string.strip())
        if not match:
            raise VersionError(f"Invalid version format: {version_string}. Expected format: v1.2.3 or 1.2.3")
        
        major, minor, patch = match.groups()
        return int(major), int(minor), int(patch)
    
    def compare_versions(self, version1: str, version2: str) -> int:
        """
        Compare two semantic versions.
        
        Args:
            version1: First version string
            version2: Second version string
            
        Returns:
            -1 if version1 < version2
             0 if version1 == version2
             1 if version1 > version2
             
        Raises:
            VersionError: If either version string is invalid
        """
        try:
            major1, minor1, patch1 = self.parse_version(version1)
            major2, minor2, patch2 = self.parse_version(version2)
        except VersionError as e:
            raise VersionError(f"Cannot compare versions: {e}")
        
        v1 = Version(major1, minor1, patch1)
        v2 = Version(major2, minor2, patch2)
        
        if v1 < v2:
            return -1
        elif v1 > v2:
            return 1
        else:
            return 0
    
    def find_highest_version(self, versions: List[str]) -> str:
        """
        Find the highest semantic version from a list of version strings.
        
        Args:
            versions: List of version strings
            
        Returns:
            The highest version string from the list
            
        Raises:
            VersionError: If no valid versions found or list is empty
        """
        if not versions:
            raise VersionError("Cannot find highest version from empty list")
        
        valid_versions = []
        for version in versions:
            try:
                major, minor, patch = self.parse_version(version)
                # Preserve original prefix (v or no v)
                prefix = "v" if version.strip().startswith("v") else ""
                valid_versions.append((Version(major, minor, patch, prefix), version))
            except VersionError:
                # Skip invalid versions but continue processing
                continue
        
        if not valid_versions:
            raise VersionError("No valid versions found in the provided list")
        
        # Sort by Version object and return the original string of the highest
        highest_version_obj, highest_version_str = max(valid_versions, key=lambda x: x[0])
        return highest_version_str
    
    def increment_patch(self, version: str) -> str:
        """
        Increment patch version (e.g., v1.2.3 -> v1.2.4).
        
        Args:
            version: Current version string
            
        Returns:
            New version string with incremented patch
            
        Raises:
            VersionError: If version string is invalid
        """
        major, minor, patch = self.parse_version(version)
        prefix = "v" if version.strip().startswith("v") else ""
        return f"{prefix}{major}.{minor}.{patch + 1}"
    
    def increment_minor(self, version: str) -> str:
        """
        Increment minor version and reset patch to 0 (e.g., v1.2.3 -> v1.3.0).
        
        Args:
            version: Current version string
            
        Returns:
            New version string with incremented minor and reset patch
            
        Raises:
            VersionError: If version string is invalid
        """
        major, minor, patch = self.parse_version(version)
        prefix = "v" if version.strip().startswith("v") else ""
        return f"{prefix}{major}.{minor + 1}.0"
    
    def increment_major(self, version: str) -> str:
        """
        Increment major version and reset minor and patch to 0 (e.g., v1.2.3 -> v2.0.0).
        
        Args:
            version: Current version string
            
        Returns:
            New version string with incremented major and reset minor/patch
            
        Raises:
            VersionError: If version string is invalid
        """
        major, minor, patch = self.parse_version(version)
        prefix = "v" if version.strip().startswith("v") else ""
        return f"{prefix}{major + 1}.0.0"


class FileManager:
    """Handles file operations and pattern matching for version management"""
    
    def __init__(self, version_files_config: List[Dict]):
        """
        Initialize FileManager with VERSION_FILES configuration.
        
        Args:
            version_files_config: List of file configuration dictionaries
            
        Raises:
            FileError: If configuration is invalid
        """
        if not version_files_config:
            raise FileError("VERSION_FILES configuration cannot be empty")
        
        self.file_configs = []
        for config in version_files_config:
            self._validate_config(config)
            file_config = FileConfig(
                file_pattern=config['file'],
                regex_pattern=config['pattern'],
                template=config['template']
            )
            self.file_configs.append(file_config)
    
    def _validate_config(self, config: Dict) -> None:
        """
        Validate a single file configuration entry.
        
        Args:
            config: Configuration dictionary to validate
            
        Raises:
            FileError: If configuration is invalid
        """
        required_keys = ['file', 'pattern', 'template']
        for key in required_keys:
            if key not in config:
                raise FileError(f"Missing required configuration key: {key}")
        
        if not isinstance(config['pattern'], re.Pattern):
            raise FileError(f"Pattern must be a compiled regex object, got {type(config['pattern'])}")
        
        if not isinstance(config['template'], str):
            raise FileError(f"Template must be a string, got {type(config['template'])}")
        
        if '{version}' not in config['template']:
            raise FileError(f"Template must contain {{version}} placeholder: {config['template']}")
        
        # Validate that regex pattern has at least one capture group
        if config['pattern'].groups < 1:
            raise FileError(f"Regex pattern must have at least one capture group: {config['pattern'].pattern}")
    
    def expand_file_patterns(self) -> List[str]:
        """
        Expand glob patterns to actual file paths.
        
        Returns:
            List of actual file paths that match the configured patterns
        """
        expanded_files = []
        
        for file_config in self.file_configs:
            pattern = file_config.file_pattern
            
            if '*' in pattern or '?' in pattern:
                # Handle glob patterns
                matched_files = glob.glob(pattern, recursive=True)
                if matched_files:
                    expanded_files.extend(matched_files)
                else:
                    # No files match the pattern - this might be expected
                    continue
            else:
                # Direct file path
                if os.path.exists(pattern):
                    expanded_files.append(pattern)
        
        # Remove duplicates and sort
        return sorted(list(set(expanded_files)))
    
    def find_versions_in_files(self) -> Dict[str, str]:
        """
        Find current versions in all configured files.
        
        Returns:
            Dictionary mapping file paths to found version strings
            
        Raises:
            FileError: If file cannot be read
        """
        versions_found = {}
        expanded_files = self.expand_file_patterns()
        
        for file_path in expanded_files:
            # Find the matching configuration for this file
            matching_config = None
            for config in self.file_configs:
                if self._file_matches_pattern(file_path, config.file_pattern):
                    matching_config = config
                    break
            
            if not matching_config:
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Search for version using the regex pattern
                match = matching_config.regex_pattern.search(content)
                if match:
                    # Extract version from first capture group
                    version = match.group(1)
                    versions_found[file_path] = version
                
            except IOError as e:
                raise FileError(f"Cannot read file {file_path}: {e}")
            except UnicodeDecodeError as e:
                raise FileError(f"Cannot decode file {file_path}: {e}")
        
        return versions_found
    
    def _file_matches_pattern(self, file_path: str, pattern: str) -> bool:
        """
        Check if a file path matches a given pattern (including glob patterns).
        
        Args:
            file_path: Path to check
            pattern: Pattern to match against (may include wildcards)
            
        Returns:
            True if file matches pattern, False otherwise
        """
        if '*' in pattern or '?' in pattern:
            # Use glob-style matching
            import fnmatch
            return fnmatch.fnmatch(file_path, pattern)
        else:
            # Direct string comparison
            return file_path == pattern
    
    def update_file_version(self, file_path: str, new_version: str) -> bool:
        """
        Update version in a specific file using its pattern and template.
        
        Args:
            file_path: Path to the file to update
            new_version: New version string to set
            
        Returns:
            True if file was updated successfully, False otherwise
            
        Raises:
            FileError: If file cannot be read/written or no matching config found
        """
        # Find the matching configuration for this file
        matching_config = None
        for config in self.file_configs:
            if self._file_matches_pattern(file_path, config.file_pattern):
                matching_config = config
                break
        
        if not matching_config:
            raise FileError(f"No configuration found for file: {file_path}")
        
        try:
            # Read current file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find current version using regex
            match = matching_config.regex_pattern.search(content)
            if not match:
                # No version found in file - this might be expected for new files
                return False
            
            # Replace the matched text with new version using template
            old_match = match.group(0)
            new_text = matching_config.template.format(version=new_version)
            
            # Replace the old version text with new version text
            updated_content = content.replace(old_match, new_text)
            
            # Write updated content back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            return True
            
        except IOError as e:
            raise FileError(f"Cannot access file {file_path}: {e}")
        except UnicodeDecodeError as e:
            raise FileError(f"Cannot decode file {file_path}: {e}")
        except KeyError as e:
            raise FileError(f"Template formatting error for {file_path}: {e}")
    
    def update_all_files(self, new_version: str) -> Dict[str, bool]:
        """
        Update version in all configured files.
        
        Args:
            new_version: New version string to set in all files
            
        Returns:
            Dictionary mapping file paths to update success status
        """
        results = {}
        expanded_files = self.expand_file_patterns()
        
        for file_path in expanded_files:
            try:
                success = self.update_file_version(file_path, new_version)
                results[file_path] = success
            except FileError as e:
                # Log error but continue with other files
                results[file_path] = False
                print(f"Warning: Failed to update {file_path}: {e}")
        
        return results


class GitManager:
    """Handles git integration for release management"""
    
    def __init__(self):
        """Initialize GitManager"""
        self.version_manager = VersionManager()
    
    def is_git_repository(self) -> bool:
        """
        Check if current directory is a git repository.
        
        Returns:
            True if current directory is a git repository, False otherwise
        """
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return False
    
    def get_git_tags(self) -> List[str]:
        """
        Get all git tags sorted by version.
        
        Returns:
            List of git tags sorted by semantic version (highest first)
            
        Raises:
            GitError: If git command fails or not in a git repository
        """
        if not self.is_git_repository():
            raise GitError("Not in a git repository")
        
        try:
            result = subprocess.run(
                ['git', 'tag', '-l'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise GitError(f"Git tag command failed: {result.stderr}")
            
            tags = [tag.strip() for tag in result.stdout.split('\n') if tag.strip()]
            
            if not tags:
                return []
            
            # Filter and sort tags by version
            version_tags = []
            for tag in tags:
                try:
                    # Try to parse as version to validate it's a version tag
                    self.version_manager.parse_version(tag)
                    version_tags.append(tag)
                except VersionError:
                    # Skip non-version tags
                    continue
            
            if not version_tags:
                return []
            
            # Sort by version (highest first)
            try:
                version_tags.sort(key=lambda x: self.version_manager.parse_version(x), reverse=True)
            except VersionError:
                # Fallback to string sort if version parsing fails
                version_tags.sort(reverse=True)
            
            return version_tags
            
        except subprocess.TimeoutExpired:
            raise GitError("Git tag command timed out")
        except (FileNotFoundError, OSError) as e:
            raise GitError(f"Git command failed: {e}")
    
    def get_commits_between_tags(self, tag1: str, tag2: str) -> List[Dict]:
        """
        Get commits between two git tags.
        
        Args:
            tag1: Starting tag (older)
            tag2: Ending tag (newer)
            
        Returns:
            List of commit dictionaries with hash, message, author, and date
            
        Raises:
            GitError: If git command fails or tags don't exist
        """
        if not self.is_git_repository():
            raise GitError("Not in a git repository")
        
        try:
            # Verify tags exist
            for tag in [tag1, tag2]:
                result = subprocess.run(
                    ['git', 'rev-parse', '--verify', f'{tag}^{{commit}}'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode != 0:
                    raise GitError(f"Tag '{tag}' does not exist")
            
            # Get commits between tags
            result = subprocess.run([
                'git', 'log', 
                f'{tag1}..{tag2}',
                '--pretty=format:%H|%s|%an|%ad',
                '--date=iso'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                raise GitError(f"Git log command failed: {result.stderr}")
            
            commits = []
            for line in result.stdout.split('\n'):
                if line.strip():
                    parts = line.split('|', 3)
                    if len(parts) == 4:
                        commits.append({
                            'hash': parts[0],
                            'message': parts[1],
                            'author': parts[2],
                            'date': parts[3]
                        })
            
            return commits
            
        except subprocess.TimeoutExpired:
            raise GitError("Git log command timed out")
        except (FileNotFoundError, OSError) as e:
            raise GitError(f"Git command failed: {e}")
    
    def get_commits_since_tag(self, tag: str) -> List[Dict]:
        """
        Get commits since a specific tag.
        
        Args:
            tag: Git tag to start from
            
        Returns:
            List of commit dictionaries with hash, message, author, and date
            
        Raises:
            GitError: If git command fails or tag doesn't exist
        """
        if not self.is_git_repository():
            raise GitError("Not in a git repository")
        
        try:
            # Verify tag exists
            result = subprocess.run(
                ['git', 'rev-parse', '--verify', f'{tag}^{{commit}}'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                raise GitError(f"Tag '{tag}' does not exist")
            
            # Get commits since tag
            result = subprocess.run([
                'git', 'log', 
                f'{tag}..HEAD',
                '--pretty=format:%H|%s|%an|%ad',
                '--date=iso'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                raise GitError(f"Git log command failed: {result.stderr}")
            
            commits = []
            for line in result.stdout.split('\n'):
                if line.strip():
                    parts = line.split('|', 3)
                    if len(parts) == 4:
                        commits.append({
                            'hash': parts[0],
                            'message': parts[1],
                            'author': parts[2],
                            'date': parts[3]
                        })
            
            return commits
            
        except subprocess.TimeoutExpired:
            raise GitError("Git log command timed out")
        except (FileNotFoundError, OSError) as e:
            raise GitError(f"Git command failed: {e}")
    
    def get_latest_tag(self) -> str:
        """
        Get the most recent git tag.
        
        Returns:
            The most recent version tag
            
        Raises:
            GitError: If no tags exist or git command fails
        """
        tags = self.get_git_tags()
        if not tags:
            raise GitError("No git tags found")
        
        return tags[0]  # First tag is the highest/most recent
    
    def get_current_commit_hash(self) -> str:
        """
        Get the current commit hash.
        
        Returns:
            Current commit hash (short format)
            
        Raises:
            GitError: If git command fails
        """
        if not self.is_git_repository():
            raise GitError("Not in a git repository")
        
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--short', 'HEAD'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                raise GitError(f"Git rev-parse command failed: {result.stderr}")
            
            return result.stdout.strip()
            
        except subprocess.TimeoutExpired:
            raise GitError("Git rev-parse command timed out")
        except (FileNotFoundError, OSError) as e:
            raise GitError(f"Git command failed: {e}")
    
    def get_all_commits_since_beginning(self) -> List[Dict]:
        """
        Get all commits from the beginning of the repository.
        
        Returns:
            List of all commit dictionaries with hash, message, author, and date
            
        Raises:
            GitError: If git command fails
        """
        if not self.is_git_repository():
            raise GitError("Not in a git repository")
        
        try:
            result = subprocess.run([
                'git', 'log', 
                '--pretty=format:%H|%s|%an|%ad',
                '--date=iso'
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                raise GitError(f"Git log command failed: {result.stderr}")
            
            commits = []
            for line in result.stdout.split('\n'):
                if line.strip():
                    parts = line.split('|', 3)
                    if len(parts) == 4:
                        commits.append({
                            'hash': parts[0],
                            'message': parts[1],
                            'author': parts[2],
                            'date': parts[3]
                        })
            
            return commits
            
        except subprocess.TimeoutExpired:
            raise GitError("Git log command timed out")
        except (FileNotFoundError, OSError) as e:
            raise GitError(f"Git command failed: {e}")


# VERSION_FILES Configuration
# 
# This configuration defines which files to scan and update for version management.
# Each entry must contain:
# - 'file': File path or glob pattern (e.g., 'app.py', '*.py', 'src/**/*.py')
# - 'pattern': Compiled regex with version in first capture group
# - 'template': String template with {version} placeholder for replacement
#
# Common patterns and examples:
VERSION_FILES = [
    # README.md version badge or documentation
    {
        'file': 'README.md', 
        'pattern': re.compile(r'- Version (v\d+\.\d+\.\d+)'),
        'template': '- Version {version}',
    },
    
    # Python files with version variable (quoted)
    {
        'file': 'sample/*.py',
        'pattern': re.compile(r'version = "(v\d+\.\d+\.\d+)"'),
        'template': 'version = "{version}"',
    },
    
    # Python files with version comment
    {
        'file': 'sample/*.py',
        'pattern': re.compile(r'Version: (v\d+\.\d+\.\d+)'),
        'template': 'Version: {version}',
    },
    
    # Additional common patterns (commented out - uncomment and modify as needed):
    
    # Python __init__.py files
    # {
    #     'file': 'src/*/__init__.py',
    #     'pattern': re.compile(r'__version__ = "(v\d+\.\d+\.\d+)"'),
    #     'template': '__version__ = "{version}"',
    # },
    
    # setup.py or pyproject.toml version
    # {
    #     'file': 'setup.py',
    #     'pattern': re.compile(r'version="(v\d+\.\d+\.\d+)"'),
    #     'template': 'version="{version}"',
    # },
    
    # package.json for Node.js projects
    # {
    #     'file': 'package.json',
    #     'pattern': re.compile(r'"version": "(v\d+\.\d+\.\d+)"'),
    #     'template': '"version": "{version}"',
    # },
    
    # Docker files
    # {
    #     'file': 'Dockerfile',
    #     'pattern': re.compile(r'LABEL version="(v\d+\.\d+\.\d+)"'),
    #     'template': 'LABEL version="{version}"',
    # },
    
    # Configuration files (YAML, JSON, etc.)
    # {
    #     'file': 'config/*.yaml',
    #     'pattern': re.compile(r'version: (v\d+\.\d+\.\d+)'),
    #     'template': 'version: {version}',
    # },
]


def validate_version_files_config(config: List[Dict]) -> None:
    """
    Validate VERSION_FILES configuration to ensure all required fields are present
    and properly formatted.
    
    Args:
        config: List of configuration dictionaries to validate
        
    Raises:
        FileError: If configuration is invalid
    """
    if not config:
        raise FileError("VERSION_FILES configuration cannot be empty")
    
    required_keys = ['file', 'pattern', 'template']
    
    for i, entry in enumerate(config):
        if not isinstance(entry, dict):
            raise FileError(f"Configuration entry {i} must be a dictionary")
        
        # Check required keys
        for key in required_keys:
            if key not in entry:
                raise FileError(f"Configuration entry {i} missing required key: '{key}'")
        
        # Validate file path
        if not isinstance(entry['file'], str) or not entry['file'].strip():
            raise FileError(f"Configuration entry {i}: 'file' must be a non-empty string")
        
        # Validate pattern is compiled regex
        if not isinstance(entry['pattern'], re.Pattern):
            raise FileError(f"Configuration entry {i}: 'pattern' must be a compiled regex (use re.compile())")
        
        # Validate pattern has at least one capture group
        if entry['pattern'].groups < 1:
            raise FileError(f"Configuration entry {i}: regex pattern must have at least one capture group for version")
        
        # Validate template
        if not isinstance(entry['template'], str):
            raise FileError(f"Configuration entry {i}: 'template' must be a string")
        
        if '{version}' not in entry['template']:
            raise FileError(f"Configuration entry {i}: template must contain '{{version}}' placeholder")
        
        # Warn about potential issues
        if '*' in entry['file'] and not any(char in entry['file'] for char in ['/', '\\']):
            print(f"Warning: Configuration entry {i} uses wildcard without directory - consider being more specific")


# Validate configuration on module load
try:
    validate_version_files_config(VERSION_FILES)
except FileError as e:
    print(f"Error in VERSION_FILES configuration: {e}")
    sys.exit(1)


class CLIInterface:
    """Main CLI interface for v-and-r tool with argument parsing and command execution"""
    
    def __init__(self):
        """Initialize CLI interface with managers"""
        self.version_manager = VersionManager()
        self.file_manager = FileManager(VERSION_FILES)
        self.git_manager = GitManager()
    
    def parse_arguments(self) -> argparse.Namespace:
        """
        Parse command-line arguments and return parsed namespace.
        
        Returns:
            Parsed arguments namespace
            
        Raises:
            SystemExit: If invalid arguments provided or help requested
        """
        parser = argparse.ArgumentParser(
            prog='v-and-r',
            description='Version and Release Manager - Automate version management and release processes',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  v-and-r                    # View current versions (default)
  v-and-r -v                 # View current versions
  v-and-r --view             # View current versions
  v-and-r -p                 # Increment patch version
  v-and-r --patch            # Increment patch version
  v-and-r -mi                # Increment minor version
  v-and-r --minor            # Increment minor version
  v-and-r -ma                # Increment major version
  v-and-r --major            # Increment major version
  v-and-r -r                 # Generate release information
  v-and-r --release-info     # Generate release information
  v-and-r -rd v1.0.0 v1.1.0  # Show commits between tags
  v-and-r --release-diff v1.0.0 v1.1.0  # Show commits between tags
  v-and-r -rl                # Show commits since last tag
  v-and-r --release-last     # Show commits since last tag
  v-and-r -rp                # Prepare release documentation
  v-and-r --release-prepare  # Prepare release documentation

Configuration:
  The tool uses VERSION_FILES configuration embedded in the script.
  Modify the VERSION_FILES array to customize file patterns, regex patterns,
  and templates for your project structure.
            """
        )
        
        # Create mutually exclusive group for main commands
        command_group = parser.add_mutually_exclusive_group()
        
        # View command (default)
        command_group.add_argument(
            '-v', '--view',
            action='store_true',
            help='View current versions across all configured files (default behavior)'
        )
        
        # Version increment commands
        command_group.add_argument(
            '-p', '--patch',
            action='store_true',
            help='Increment patch version (e.g., v1.2.3 -> v1.2.4)'
        )
        
        command_group.add_argument(
            '-mi', '--minor',
            action='store_true',
            help='Increment minor version and reset patch (e.g., v1.2.3 -> v1.3.0)'
        )
        
        command_group.add_argument(
            '-ma', '--major',
            action='store_true',
            help='Increment major version and reset minor/patch (e.g., v1.2.3 -> v2.0.0)'
        )
        
        # Release management commands
        command_group.add_argument(
            '-r', '--release-info',
            action='store_true',
            help='Generate release information and version.json file'
        )
        
        command_group.add_argument(
            '-rd', '--release-diff',
            nargs=2,
            metavar=('TAG1', 'TAG2'),
            help='Show commits between two git tags (TAG1 to TAG2)'
        )
        
        command_group.add_argument(
            '-rl', '--release-last',
            action='store_true',
            help='Show commits since the last git tag'
        )
        
        command_group.add_argument(
            '-rp', '--release-prepare',
            action='store_true',
            help='Prepare release documentation (update version.json, CHANGELOG.md, RELEASES.md)'
        )
        
        # Debug and utility flags (not mutually exclusive)
        parser.add_argument(
            '-d', '--debug',
            action='store_true',
            help='Enable debug logging for troubleshooting'
        )
        
        # Parse arguments
        args = parser.parse_args()
        
        # Validate argument combinations
        self._validate_arguments(args)
        
        return args
    
    def _validate_arguments(self, args: argparse.Namespace) -> None:
        """
        Validate parsed arguments for invalid combinations.
        
        Args:
            args: Parsed arguments namespace
            
        Raises:
            SystemExit: If invalid argument combinations detected
        """
        # Check for release-diff argument validation
        if args.release_diff:
            tag1, tag2 = args.release_diff
            if not tag1 or not tag2:
                print("Error: Both TAG1 and TAG2 must be provided for --release-diff")
                sys.exit(1)
            
            if tag1 == tag2:
                print("Error: TAG1 and TAG2 cannot be the same for --release-diff")
                sys.exit(1)
        
        # If no command specified, default to view
        if not any([
            args.view, args.patch, args.minor, args.major,
            args.release_info, args.release_diff, args.release_last,
            args.release_prepare
        ]):
            args.view = True
    
    def execute_command(self, args: argparse.Namespace) -> int:
        """
        Execute the appropriate command based on parsed arguments.
        
        Args:
            args: Parsed arguments namespace
            
        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        logger = logging.getLogger('v-and-r')
        
        # Log the command being executed
        command_name = "view"  # default
        if args.patch:
            command_name = "patch"
        elif args.minor:
            command_name = "minor"
        elif args.major:
            command_name = "major"
        elif args.release_info:
            command_name = "release-info"
        elif args.release_diff:
            command_name = f"release-diff {args.release_diff[0]} {args.release_diff[1]}"
        elif args.release_last:
            command_name = "release-last"
        elif args.release_prepare:
            command_name = "release-prepare"
        
        logger.info(f"Executing command: {command_name}")
        
        # Execute the appropriate command (error handling is done at higher level)
        if args.view:
            return self._execute_view_command()
        elif args.patch:
            return self._execute_increment_command('patch')
        elif args.minor:
            return self._execute_increment_command('minor')
        elif args.major:
            return self._execute_increment_command('major')
        elif args.release_info:
            return self._execute_release_info_command()
        elif args.release_diff:
            return self._execute_release_diff_command(args.release_diff[0], args.release_diff[1])
        elif args.release_last:
            return self._execute_release_last_command()
        elif args.release_prepare:
            return self._execute_release_prepare_command()
        else:
            # Default to view if no command specified
            return self._execute_view_command()
    
    def _execute_view_command(self) -> int:
        """
        Execute view command to display current versions.
        
        Returns:
            Exit code (0 for success, 1 for failure)
        """
        logger = logging.getLogger('v-and-r')
        logger.debug("Executing view command")
        
        print("v-and-r (Version and Release Manager)")
        print("=" * 50)
        print("Current versions across configured files:")
        print()
        
        logger.debug("Scanning files for versions")
        versions_found = self.file_manager.find_versions_in_files()
        logger.debug(f"Found versions in {len(versions_found)} files")
        
        if not versions_found:
            logger.info("No versions found in any configured files")
            print("No versions found in any configured files.")
            print("\nConfigured file patterns:")
            for config in self.file_manager.file_configs:
                print(f"  - {config.file_pattern}")
            return 0
        
        # Display found versions
        for file_path, version in versions_found.items():
            print(f"  {file_path}: {version}")
            logger.debug(f"Found version {version} in {file_path}")
        
        # Highlight highest version if multiple versions exist
        if len(versions_found) > 1:
            try:
                highest_version = self.version_manager.find_highest_version(list(versions_found.values()))
                print(f"\nHighest version: {highest_version}")
                logger.debug(f"Highest version determined: {highest_version}")
            except VersionError as e:
                print(f"\nWarning: Could not determine highest version: {e}")
                logger.warning(f"Could not determine highest version: {e}")
        
        logger.info("View command completed successfully")
        return 0
    
    def _execute_increment_command(self, increment_type: str) -> int:
        """
        Execute version increment command with rollback mechanism and confirmation.
        
        Args:
            increment_type: Type of increment ('patch', 'minor', 'major')
            
        Returns:
            Exit code (0 for success, 1 for failure)
        """
        print(f"v-and-r: Incrementing {increment_type} version")
        print("=" * 50)
        
        try:
            # Find current versions
            versions_found = self.file_manager.find_versions_in_files()
            
            if not versions_found:
                print("Error: No versions found in configured files.")
                print("\nConfigured file patterns:")
                for config in self.file_manager.file_configs:
                    print(f"  - {config.file_pattern}")
                return 1
            
            # Display current versions
            print("Current versions found:")
            for file_path, version in versions_found.items():
                print(f"  {file_path}: {version}")
            print()
            
            # Find highest version
            current_version = self.version_manager.find_highest_version(list(versions_found.values()))
            print(f"Current highest version: {current_version}")
            
            # Calculate new version
            if increment_type == 'patch':
                new_version = self.version_manager.increment_patch(current_version)
            elif increment_type == 'minor':
                new_version = self.version_manager.increment_minor(current_version)
            elif increment_type == 'major':
                new_version = self.version_manager.increment_major(current_version)
            else:
                raise ValueError(f"Invalid increment type: {increment_type}")
            
            print(f"New version will be: {new_version}")
            print()
            
            # Get confirmation from user
            try:
                confirmation = input(f"Proceed with {increment_type} version increment to {new_version}? (y/N): ").strip().lower()
                if confirmation not in ['y', 'yes']:
                    print("Operation cancelled by user.")
                    return 0
            except (EOFError, KeyboardInterrupt):
                print("\nOperation cancelled by user.")
                return 0
            
            print()
            print("Updating files...")
            
            # Store original file contents for rollback
            original_contents = {}
            files_to_update = self.file_manager.expand_file_patterns()
            
            # Read original contents before making changes
            for file_path in files_to_update:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        original_contents[file_path] = f.read()
                except (IOError, UnicodeDecodeError) as e:
                    print(f"Warning: Could not read {file_path} for backup: {e}")
            
            # Update all files with rollback capability
            update_results = {}
            failed_files = []
            
            for file_path in files_to_update:
                try:
                    success = self.file_manager.update_file_version(file_path, new_version)
                    update_results[file_path] = success
                    
                    status = "✓" if success else "○"
                    status_text = "updated" if success else "no version found"
                    print(f"  {status} {file_path} - {status_text}")
                    
                    if not success:
                        # File had no version to update - this is not necessarily an error
                        continue
                        
                except FileError as e:
                    update_results[file_path] = False
                    failed_files.append((file_path, str(e)))
                    print(f"  ✗ {file_path} - failed: {e}")
            
            print()
            
            # Check if any critical failures occurred
            if failed_files:
                print(f"Warning: {len(failed_files)} files failed to update:")
                for file_path, error in failed_files:
                    print(f"  - {file_path}: {error}")
                print()
                
                # Ask if user wants to rollback
                try:
                    rollback_choice = input("Some files failed to update. Rollback all changes? (y/N): ").strip().lower()
                    if rollback_choice in ['y', 'yes']:
                        print("Rolling back changes...")
                        self._rollback_file_changes(original_contents, update_results)
                        print("All changes have been rolled back.")
                        return 1
                except (EOFError, KeyboardInterrupt):
                    print("\nNo rollback performed.")
            
            # Count successful updates
            successful_updates = sum(1 for success in update_results.values() if success)
            total_files = len(update_results)
            files_with_versions = sum(1 for file_path in files_to_update 
                                    if file_path in versions_found or 
                                    update_results.get(file_path, False))
            
            # Report results
            if successful_updates > 0:
                print(f"✓ Successfully updated {successful_updates} files to version {new_version}")
                if failed_files:
                    print(f"  Note: {len(failed_files)} files had errors but changes were not rolled back")
                
                # Show summary of what was updated
                print("\nSummary:")
                print(f"  - Files processed: {total_files}")
                print(f"  - Files updated: {successful_updates}")
                print(f"  - Files with errors: {len(failed_files)}")
                print(f"  - Files without versions: {total_files - files_with_versions}")
                
                return 0 if not failed_files else 1
            else:
                print("✗ No files were successfully updated.")
                if original_contents:
                    print("Rolling back any partial changes...")
                    self._rollback_file_changes(original_contents, update_results)
                return 1
                
        except (VersionError, FileError) as e:
            print(f"Error: {e}")
            return 1
        except Exception as e:
            print(f"Unexpected error during version increment: {e}")
            return 1
    
    def _rollback_file_changes(self, original_contents: Dict[str, str], update_results: Dict[str, bool]) -> None:
        """
        Rollback file changes using stored original contents.
        
        Args:
            original_contents: Dictionary mapping file paths to their original content
            update_results: Dictionary mapping file paths to update success status
        """
        rollback_count = 0
        rollback_errors = []
        
        for file_path, original_content in original_contents.items():
            # Only rollback files that were successfully updated
            if update_results.get(file_path, False):
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(original_content)
                    rollback_count += 1
                    print(f"  ✓ Rolled back {file_path}")
                except (IOError, UnicodeDecodeError) as e:
                    rollback_errors.append((file_path, str(e)))
                    print(f"  ✗ Failed to rollback {file_path}: {e}")
        
        if rollback_errors:
            print(f"\nWarning: {len(rollback_errors)} files could not be rolled back:")
            for file_path, error in rollback_errors:
                print(f"  - {file_path}: {error}")
        else:
            print(f"\nSuccessfully rolled back {rollback_count} files.")
    
    def generate_release_info(self) -> ReleaseInfo:
        """
        Generate release information with git integration and graceful degradation.
        
        Returns:
            ReleaseInfo object with version, timestamp, commit hash, and commits
            
        Raises:
            VAndRError: If unable to determine current version or generate release info
        """
        import datetime
        
        # Get current version from files
        try:
            versions_found = self.file_manager.find_versions_in_files()
            if not versions_found:
                raise VAndRError("No versions found in configured files")
            
            current_version = self.version_manager.find_highest_version(list(versions_found.values()))
        except (FileError, VersionError) as e:
            raise VAndRError(f"Cannot determine current version: {e}")
        
        # Generate timestamp
        timestamp = datetime.datetime.now().isoformat()
        
        # Initialize git-related variables with defaults
        commit_hash = "unknown"
        commits = []
        previous_version = None
        
        # Try to get git information with graceful degradation
        if self.git_manager.is_git_repository():
            try:
                # Get current commit hash
                commit_hash = self.git_manager.get_current_commit_hash()
                
                # Try to get previous version from git tags
                try:
                    tags = self.git_manager.get_git_tags()
                    if tags:
                        # Find the previous version tag (not the current one)
                        for tag in tags:
                            if tag != current_version:
                                previous_version = tag
                                break
                        
                        # Get commits since previous version or all commits if no previous version
                        if previous_version:
                            commits = self.git_manager.get_commits_since_tag(previous_version)
                        else:
                            # No previous version, get all commits
                            commits = self.git_manager.get_all_commits_since_beginning()
                    else:
                        # No tags exist, get all commits
                        commits = self.git_manager.get_all_commits_since_beginning()
                        
                except GitError as e:
                    # Git tag operations failed, but we can still get basic info
                    print(f"Warning: Could not retrieve git tag information: {e}")
                    try:
                        # Fallback to getting all commits
                        commits = self.git_manager.get_all_commits_since_beginning()
                    except GitError:
                        # Even basic git operations failed
                        print("Warning: Could not retrieve commit history")
                        commits = []
                        
            except GitError as e:
                # Git operations failed, use defaults
                print(f"Warning: Git integration failed: {e}")
                commit_hash = "unknown"
                commits = []
        else:
            print("Warning: Not in a git repository - using basic release info")
        
        return ReleaseInfo(
            version=current_version,
            timestamp=timestamp,
            commit_hash=commit_hash,
            commits=commits,
            previous_version=previous_version
        )
    
    def _update_version_json(self, release_info: ReleaseInfo) -> None:
        """
        Update version.json file with release information.
        
        Args:
            release_info: ReleaseInfo object containing version and metadata
            
        Raises:
            FileError: If unable to write version.json file
        """
        try:
            with open('version.json', 'w', encoding='utf-8') as f:
                f.write(release_info.to_json())
            print("✓ version.json updated successfully")
        except IOError as e:
            raise FileError(f"Cannot write version.json: {e}")
    
    def _update_changelog(self, release_info: ReleaseInfo) -> None:
        """
        Update CHANGELOG.md file with new release information.
        Preserves existing content and adds new release at the top.
        
        Args:
            release_info: ReleaseInfo object containing version and commit information
            
        Raises:
            FileError: If unable to read or write CHANGELOG.md file
        """
        changelog_path = 'CHANGELOG.md'
        
        # Read existing changelog if it exists
        existing_content = ""
        if os.path.exists(changelog_path):
            try:
                with open(changelog_path, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
            except IOError as e:
                raise FileError(f"Cannot read existing CHANGELOG.md: {e}")
        
        # Generate new changelog entry
        new_entry = self._generate_changelog_entry(release_info)
        
        # Create new changelog content
        if existing_content:
            # Find where to insert new entry (after header, before first version)
            lines = existing_content.split('\n')
            insert_index = 0
            
            # Skip header lines and find insertion point
            for i, line in enumerate(lines):
                if line.strip().startswith('## [') or line.strip().startswith('## '):
                    insert_index = i
                    break
                elif line.strip() == '':
                    continue
                elif line.strip().startswith('#'):
                    continue
                else:
                    insert_index = i
                    break
            
            # Insert new entry
            lines.insert(insert_index, new_entry)
            new_content = '\n'.join(lines)
        else:
            # Create new changelog file
            header = """# Changelog
All notable changes to this project will be documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

"""
            new_content = header + new_entry
        
        # Write updated changelog
        try:
            with open(changelog_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print("✓ CHANGELOG.md updated successfully")
        except IOError as e:
            raise FileError(f"Cannot write CHANGELOG.md: {e}")
    
    def _generate_changelog_entry(self, release_info: ReleaseInfo) -> str:
        """
        Generate a changelog entry for the release.
        
        Args:
            release_info: ReleaseInfo object containing version and commit information
            
        Returns:
            Formatted changelog entry string
        """
        from datetime import datetime
        
        # Parse timestamp to get date
        try:
            dt = datetime.fromisoformat(release_info.timestamp.replace('Z', '+00:00'))
            date_str = dt.strftime('%Y-%m-%d')
        except:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        # Start building the entry
        entry_lines = [f"## [{release_info.version}] - {date_str}"]
        
        if not release_info.commits:
            entry_lines.extend([
                "### Changed",
                "- Version bump to " + release_info.version,
                ""
            ])
            return '\n'.join(entry_lines)
        
        # Group commits by type
        commit_groups = {
            'Added': [],
            'Changed': [],
            'Fixed': [],
            'Removed': [],
            'Security': [],
            'Other': []
        }
        
        for commit in release_info.commits:
            message = commit['message'].strip()
            hash_short = commit['hash'][:7] if len(commit['hash']) >= 7 else commit['hash']
            
            # Categorize commits based on conventional commit prefixes
            if message.lower().startswith(('feat:', 'feature:')):
                clean_message = message[message.find(':') + 1:].strip()
                commit_groups['Added'].append(f"- {clean_message} ({hash_short})")
            elif message.lower().startswith(('fix:', 'bugfix:')):
                clean_message = message[message.find(':') + 1:].strip()
                commit_groups['Fixed'].append(f"- {clean_message} ({hash_short})")
            elif message.lower().startswith(('docs:', 'doc:')):
                clean_message = message[message.find(':') + 1:].strip()
                commit_groups['Changed'].append(f"- Documentation: {clean_message} ({hash_short})")
            elif message.lower().startswith(('refactor:', 'style:')):
                clean_message = message[message.find(':') + 1:].strip()
                commit_groups['Changed'].append(f"- {clean_message} ({hash_short})")
            elif message.lower().startswith(('remove:', 'rm:')):
                clean_message = message[message.find(':') + 1:].strip()
                commit_groups['Removed'].append(f"- {clean_message} ({hash_short})")
            elif message.lower().startswith('security:'):
                clean_message = message[message.find(':') + 1:].strip()
                commit_groups['Security'].append(f"- {clean_message} ({hash_short})")
            else:
                commit_groups['Other'].append(f"- {message} ({hash_short})")
        
        # Add non-empty groups to entry
        for group_name, group_commits in commit_groups.items():
            if group_commits:
                entry_lines.append(f"### {group_name}")
                entry_lines.extend(group_commits)
                entry_lines.append("")
        
        # Add commits section with formatted git log style
        if release_info.commits:
            entry_lines.extend([
                "### Commits",
                "```"
            ])
            
            for commit in release_info.commits:
                hash_short = commit['hash'][:7] if len(commit['hash']) >= 7 else commit['hash']
                author = commit['author']
                date = commit['date'][:10] if len(commit['date']) >= 10 else commit['date']
                message = commit['message']
                
                # Format similar to git log --oneline with additional info
                entry_lines.append(f"{hash_short} {message:<60}\t{author}\t{date}")
            
            entry_lines.extend([
                "```",
                ""
            ])
        
        return '\n'.join(entry_lines)
    
    def _update_releases(self, release_info: ReleaseInfo) -> None:
        """
        Update RELEASES.md file with new release summary.
        Preserves existing content and adds new release at the top.
        
        Args:
            release_info: ReleaseInfo object containing version and commit information
            
        Raises:
            FileError: If unable to read or write RELEASES.md file
        """
        releases_path = 'RELEASES.md'
        
        # Read existing releases file if it exists
        existing_content = ""
        if os.path.exists(releases_path):
            try:
                with open(releases_path, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
            except IOError as e:
                raise FileError(f"Cannot read existing RELEASES.md: {e}")
        
        # Generate new release entry
        new_entry = self._generate_releases_entry(release_info)
        
        # Create new releases content
        if existing_content:
            # Find where to insert new entry (after header, before first release)
            lines = existing_content.split('\n')
            insert_index = 0
            
            # Skip header lines and find insertion point
            for i, line in enumerate(lines):
                if line.strip().startswith('## ') and not line.strip().startswith('## Release'):
                    insert_index = i
                    break
                elif line.strip() == '':
                    continue
                elif line.strip().startswith('#'):
                    continue
                else:
                    insert_index = i
                    break
            
            # Insert new entry
            lines.insert(insert_index, new_entry)
            new_content = '\n'.join(lines)
        else:
            # Create new releases file
            header = """# Releases

This document contains release notes and highlights for each version.

"""
            new_content = header + new_entry
        
        # Write updated releases file
        try:
            with open(releases_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print("✓ RELEASES.md updated successfully")
        except IOError as e:
            raise FileError(f"Cannot write RELEASES.md: {e}")
    
    def _generate_releases_entry(self, release_info: ReleaseInfo) -> str:
        """
        Generate a release entry for RELEASES.md.
        
        Args:
            release_info: ReleaseInfo object containing version and commit information
            
        Returns:
            Formatted release entry string
        """
        from datetime import datetime
        
        # Parse timestamp to get date
        try:
            dt = datetime.fromisoformat(release_info.timestamp.replace('Z', '+00:00'))
            date_str = dt.strftime('%Y-%m-%d')
        except:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        # Start building the entry
        entry_lines = [
            f"## {release_info.version} - {date_str}",
            ""
        ]
        
        if not release_info.commits:
            entry_lines.extend([
                "Version bump release.",
                ""
            ])
            return '\n'.join(entry_lines)
        
        # Generate summary statistics
        total_commits = len(release_info.commits)
        contributors = set(commit['author'] for commit in release_info.commits)
        
        # Count commit types
        features = sum(1 for c in release_info.commits if c['message'].lower().startswith(('feat:', 'feature:')))
        fixes = sum(1 for c in release_info.commits if c['message'].lower().startswith(('fix:', 'bugfix:')))
        docs = sum(1 for c in release_info.commits if c['message'].lower().startswith(('docs:', 'doc:')))
        other = total_commits - features - fixes - docs
        
        # Add summary
        entry_lines.extend([
            f"**{total_commits} commits** from **{len(contributors)} contributors**",
            ""
        ])
        
        if release_info.previous_version:
            entry_lines.extend([
                f"Changes since {release_info.previous_version}:",
                ""
            ])
        
        # Add breakdown
        breakdown = []
        if features > 0:
            breakdown.append(f"{features} new features")
        if fixes > 0:
            breakdown.append(f"{fixes} bug fixes")
        if docs > 0:
            breakdown.append(f"{docs} documentation updates")
        if other > 0:
            breakdown.append(f"{other} other changes")
        
        if breakdown:
            entry_lines.extend([
                "**Highlights:**",
                "- " + ", ".join(breakdown),
                ""
            ])
        
        # Add key changes (first few commits)
        if release_info.commits:
            entry_lines.extend([
                "**Key Changes:**"
            ])
            
            # Show up to 5 most important commits
            important_commits = []
            
            # Prioritize features and fixes
            for commit in release_info.commits:
                if len(important_commits) >= 5:
                    break
                message = commit['message'].strip()
                if message.lower().startswith(('feat:', 'feature:', 'fix:', 'bugfix:')):
                    clean_message = message[message.find(':') + 1:].strip()
                    important_commits.append(f"- {clean_message}")
            
            # Fill remaining slots with other commits
            for commit in release_info.commits:
                if len(important_commits) >= 5:
                    break
                message = commit['message'].strip()
                if not message.lower().startswith(('feat:', 'feature:', 'fix:', 'bugfix:')):
                    important_commits.append(f"- {message}")
            
            entry_lines.extend(important_commits)
            entry_lines.append("")
        
        # Add contributors
        if contributors:
            contributor_list = sorted(contributors)
            entry_lines.extend([
                f"**Contributors:** {', '.join(contributor_list)}",
                ""
            ])
        
        # Add metadata
        entry_lines.extend([
            f"**Commit Hash:** `{release_info.commit_hash}`",
            ""
        ])
        
        return '\n'.join(entry_lines)
    
    def _format_release_notes(self, commits: List[Dict]) -> None:
        """
        Format and display release notes based on commit messages.
        
        Args:
            commits: List of commit dictionaries with hash, message, author, and date
        """
        if not commits:
            print("No commits to display.")
            return
        
        # Group commits by type if they follow conventional commit format
        commit_groups = {
            'Features': [],
            'Bug Fixes': [],
            'Documentation': [],
            'Other': []
        }
        
        for commit in commits:
            message = commit['message'].strip()
            hash_short = commit['hash'][:7] if len(commit['hash']) >= 7 else commit['hash']
            
            # Categorize commits based on conventional commit prefixes
            if message.lower().startswith(('feat:', 'feature:')):
                commit_groups['Features'].append(f"  - {message} ({hash_short})")
            elif message.lower().startswith(('fix:', 'bugfix:')):
                commit_groups['Bug Fixes'].append(f"  - {message} ({hash_short})")
            elif message.lower().startswith(('docs:', 'doc:')):
                commit_groups['Documentation'].append(f"  - {message} ({hash_short})")
            else:
                commit_groups['Other'].append(f"  - {message} ({hash_short})")
        
        # Display grouped commits
        for group_name, group_commits in commit_groups.items():
            if group_commits:
                print(f"\n{group_name}:")
                for commit_line in group_commits[:10]:  # Limit to 10 commits per group
                    print(commit_line)
                
                if len(group_commits) > 10:
                    print(f"  ... and {len(group_commits) - 10} more commits")
        
        # Show total commit count
        print(f"\nTotal commits: {len(commits)}")
        
        # Show date range if available
        if commits:
            try:
                dates = [commit['date'] for commit in commits if commit.get('date')]
                if dates:
                    # Sort dates to get range
                    sorted_dates = sorted(dates)
                    if len(sorted_dates) > 1:
                        print(f"Date range: {sorted_dates[-1][:10]} to {sorted_dates[0][:10]}")
                    else:
                        print(f"Date: {sorted_dates[0][:10]}")
            except (KeyError, IndexError, TypeError):
                # Date parsing failed, skip date range
                pass
    
    def _format_commit_history(self, commits: List[Dict], show_stats: bool = False) -> None:
        """
        Format and display commit history in a readable format.
        
        Args:
            commits: List of commit dictionaries with hash, message, author, and date
            show_stats: Whether to show additional statistics
        """
        if not commits:
            print("No commits to display.")
            return
        
        # Display commits in chronological order (newest first)
        for i, commit in enumerate(commits):
            hash_short = commit['hash'][:7] if len(commit['hash']) >= 7 else commit['hash']
            message = commit['message'].strip()
            author = commit.get('author', 'Unknown')
            date = commit.get('date', 'Unknown date')
            
            # Format date to be more readable
            try:
                # Parse ISO date and format it nicely
                if date != 'Unknown date':
                    # Extract just the date part (YYYY-MM-DD)
                    date_part = date[:10] if len(date) >= 10 else date
                else:
                    date_part = date
            except (ValueError, IndexError):
                date_part = date
            
            # Display commit with formatting
            print(f"{hash_short}  {message}")
            print(f"         Author: {author}")
            print(f"         Date: {date_part}")
            
            # Add spacing between commits, but not after the last one
            if i < len(commits) - 1:
                print()
        
        # Show statistics if requested
        if show_stats:
            print()
            print("-" * 50)
            print(f"Total commits: {len(commits)}")
            
            # Show unique authors
            authors = set(commit.get('author', 'Unknown') for commit in commits)
            print(f"Contributors: {len(authors)}")
            if len(authors) <= 5:
                print(f"  {', '.join(sorted(authors))}")
            else:
                author_list = sorted(authors)
                print(f"  {', '.join(author_list[:5])} and {len(authors) - 5} more")
            
            # Show date range
            try:
                dates = [commit['date'] for commit in commits if commit.get('date') and commit['date'] != 'Unknown date']
                if dates:
                    # Sort dates to get range (newest first in git log output)
                    sorted_dates = sorted(dates, reverse=True)
                    if len(sorted_dates) > 1:
                        newest_date = sorted_dates[0][:10]
                        oldest_date = sorted_dates[-1][:10]
                        print(f"Date range: {oldest_date} to {newest_date}")
                    else:
                        print(f"Date: {sorted_dates[0][:10]}")
            except (KeyError, IndexError, TypeError):
                # Date parsing failed, skip date range
                pass
            
            # Categorize commits by type for summary
            commit_types = {
                'Features': 0,
                'Bug Fixes': 0,
                'Documentation': 0,
                'Other': 0
            }
            
            for commit in commits:
                message = commit['message'].strip().lower()
                if message.startswith(('feat:', 'feature:')):
                    commit_types['Features'] += 1
                elif message.startswith(('fix:', 'bugfix:')):
                    commit_types['Bug Fixes'] += 1
                elif message.startswith(('docs:', 'doc:')):
                    commit_types['Documentation'] += 1
                else:
                    commit_types['Other'] += 1
            
            # Show commit type breakdown
            type_summary = []
            for commit_type, count in commit_types.items():
                if count > 0:
                    type_summary.append(f"{count} {commit_type.lower()}")
            
            if type_summary:
                print(f"Breakdown: {', '.join(type_summary)}")
    
    def _execute_release_info_command(self) -> int:
        """
        Execute release info command to generate version.json.
        
        Returns:
            Exit code (0 for success, 1 for failure)
        """
        print("v-and-r: Generating release information")
        print("=" * 50)
        
        try:
            release_info = self.generate_release_info()
            
            # Write version.json file
            version_json_path = 'version.json'
            with open(version_json_path, 'w', encoding='utf-8') as f:
                f.write(release_info.to_json())
            
            print(f"✓ Generated {version_json_path}")
            print(f"  Version: {release_info.version}")
            print(f"  Timestamp: {release_info.timestamp}")
            print(f"  Commit: {release_info.commit_hash}")
            
            if release_info.previous_version:
                print(f"  Previous version: {release_info.previous_version}")
            
            print(f"  Commits included: {len(release_info.commits)}")
            
            # Display release notes
            if release_info.commits:
                print("\nRelease Notes:")
                print("-" * 30)
                self._format_release_notes(release_info.commits)
            else:
                print("\nNo commits found for release notes.")
            
            return 0
            
        except (VAndRError, VersionError, FileError, GitError) as e:
            print(f"Error generating release info: {e}")
            return 1
        except Exception as e:
            print(f"Unexpected error: {e}")
            return 1
    
    def _execute_release_diff_command(self, tag1: str, tag2: str) -> int:
        """
        Execute release diff command to show commits between tags.
        
        Args:
            tag1: Starting tag (older)
            tag2: Ending tag (newer)
            
        Returns:
            Exit code (0 for success, 1 for failure)
        """
        print(f"v-and-r: Commits between {tag1} and {tag2}")
        print("=" * 50)
        
        try:
            # Check if we're in a git repository
            if not self.git_manager.is_git_repository():
                print("Error: Not in a git repository")
                print("This command requires git integration to function.")
                return 1
            
            # Validate that both tags exist
            try:
                # Get all available tags for reference
                available_tags = self.git_manager.get_git_tags()
                
                # Check if tags exist
                if tag1 not in available_tags:
                    print(f"Error: Tag '{tag1}' does not exist")
                    if available_tags:
                        print(f"Available tags: {', '.join(available_tags[:10])}")
                        if len(available_tags) > 10:
                            print(f"... and {len(available_tags) - 10} more")
                    else:
                        print("No git tags found in this repository")
                    return 1
                
                if tag2 not in available_tags:
                    print(f"Error: Tag '{tag2}' does not exist")
                    if available_tags:
                        print(f"Available tags: {', '.join(available_tags[:10])}")
                        if len(available_tags) > 10:
                            print(f"... and {len(available_tags) - 10} more")
                    else:
                        print("No git tags found in this repository")
                    return 1
                
            except GitError as e:
                print(f"Error retrieving git tags: {e}")
                return 1
            
            # Get commits between the tags
            try:
                commits = self.git_manager.get_commits_between_tags(tag1, tag2)
                
                if not commits:
                    print(f"No commits found between {tag1} and {tag2}")
                    print("This could mean:")
                    print(f"  - The tags are the same commit")
                    print(f"  - {tag2} is older than {tag1}")
                    print(f"  - The tags are not in the current branch history")
                    return 0
                
                # Display commit information
                print(f"Found {len(commits)} commits between {tag1} and {tag2}:")
                print()
                
                # Format and display commits
                self._format_commit_history(commits, show_stats=True)
                
                return 0
                
            except GitError as e:
                print(f"Error retrieving commits between tags: {e}")
                return 1
                
        except Exception as e:
            print(f"Unexpected error: {e}")
            return 1
    
    def _execute_release_last_command(self) -> int:
        """
        Execute release last command to show commits since last tag.
        
        Returns:
            Exit code (0 for success, 1 for failure)
        """
        print("v-and-r: Commits since last release")
        print("=" * 50)
        
        try:
            # Check if we're in a git repository
            if not self.git_manager.is_git_repository():
                print("Error: Not in a git repository")
                print("This command requires git integration to function.")
                return 1
            
            # Get the latest tag
            try:
                latest_tag = self.git_manager.get_latest_tag()
                print(f"Latest tag: {latest_tag}")
                print()
                
            except GitError as e:
                # No tags exist, show all commits from beginning
                print("No git tags found - showing all commits from repository beginning")
                print()
                
                try:
                    commits = self.git_manager.get_all_commits_since_beginning()
                    
                    if not commits:
                        print("No commits found in this repository")
                        return 0
                    
                    print(f"Found {len(commits)} total commits:")
                    print()
                    
                    # Format and display commits
                    self._format_commit_history(commits, show_stats=True)
                    
                    return 0
                    
                except GitError as git_error:
                    print(f"Error retrieving commit history: {git_error}")
                    return 1
            
            # Get commits since the latest tag
            try:
                commits = self.git_manager.get_commits_since_tag(latest_tag)
                
                if not commits:
                    print(f"No commits found since {latest_tag}")
                    print("The repository is up to date with the latest tag.")
                    return 0
                
                print(f"Found {len(commits)} commits since {latest_tag}:")
                print()
                
                # Format and display commits
                self._format_commit_history(commits, show_stats=True)
                
                return 0
                
            except GitError as e:
                print(f"Error retrieving commits since tag: {e}")
                return 1
                
        except Exception as e:
            print(f"Unexpected error: {e}")
            return 1
    
    def _execute_release_prepare_command(self) -> int:
        """
        Execute release prepare command to update documentation.
        Updates version.json, CHANGELOG.md, and RELEASES.md files.
        
        Returns:
            Exit code (0 for success, 1 for failure)
        """
        print("v-and-r: Preparing release documentation")
        print("=" * 50)
        
        try:
            # Generate release information
            print("Generating release information...")
            release_info = self.generate_release_info()
            
            # Update version.json
            print(f"Updating version.json for version {release_info.version}...")
            self._update_version_json(release_info)
            
            # Update CHANGELOG.md
            print("Updating CHANGELOG.md...")
            self._update_changelog(release_info)
            
            # Update RELEASES.md
            print("Updating RELEASES.md...")
            self._update_releases(release_info)
            
            print("\n" + "=" * 50)
            print("Release preparation completed successfully!")
            print(f"Version: {release_info.version}")
            print(f"Files updated: version.json, CHANGELOG.md, RELEASES.md")
            
            if release_info.commits:
                print(f"Commits included: {len(release_info.commits)}")
            
            return 0
            
        except (VAndRError, FileError, GitError) as e:
            print(f"Error preparing release: {e}")
            return 1
        except Exception as e:
            print(f"Unexpected error during release preparation: {e}")
            return 1


def setup_logging(debug: bool = False) -> None:
    """
    Set up logging configuration for debugging and troubleshooting.
    
    Args:
        debug: Enable debug level logging if True
    """
    log_level = logging.DEBUG if debug else logging.INFO
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stderr)
        ]
    )
    
    # Create logger for v-and-r
    logger = logging.getLogger('v-and-r')
    logger.setLevel(log_level)
    
    if debug:
        logger.debug("Debug logging enabled")


def validate_version_files_config(config: List[Dict]) -> None:
    """
    Validate VERSION_FILES configuration for completeness and correctness.
    
    Args:
        config: VERSION_FILES configuration list
        
    Raises:
        VAndRError: If configuration is invalid
    """
    logger = logging.getLogger('v-and-r')
    logger.debug("Validating VERSION_FILES configuration")
    
    if not config:
        raise VAndRError("VERSION_FILES configuration is empty. Please define at least one file pattern.")
    
    if not isinstance(config, list):
        raise VAndRError("VERSION_FILES must be a list of configuration dictionaries.")
    
    required_keys = ['file', 'pattern', 'template']
    
    for i, entry in enumerate(config):
        if not isinstance(entry, dict):
            raise VAndRError(f"VERSION_FILES entry {i} must be a dictionary, got {type(entry)}")
        
        # Check required keys
        for key in required_keys:
            if key not in entry:
                raise VAndRError(f"VERSION_FILES entry {i} missing required key: '{key}'")
        
        # Validate file pattern
        if not isinstance(entry['file'], str) or not entry['file'].strip():
            raise VAndRError(f"VERSION_FILES entry {i}: 'file' must be a non-empty string")
        
        # Validate regex pattern
        if not isinstance(entry['pattern'], re.Pattern):
            raise VAndRError(f"VERSION_FILES entry {i}: 'pattern' must be a compiled regex Pattern object")
        
        # Check that regex has at least one capture group
        if entry['pattern'].groups < 1:
            raise VAndRError(f"VERSION_FILES entry {i}: regex pattern must have at least one capture group to extract version")
        
        # Validate template
        if not isinstance(entry['template'], str) or not entry['template'].strip():
            raise VAndRError(f"VERSION_FILES entry {i}: 'template' must be a non-empty string")
        
        # Check that template contains version placeholder
        if '{version}' not in entry['template']:
            raise VAndRError(f"VERSION_FILES entry {i}: template must contain '{{version}}' placeholder")
        
        logger.debug(f"Validated config entry {i}: file='{entry['file']}', template='{entry['template']}'")
    
    logger.info(f"VERSION_FILES configuration validated successfully ({len(config)} entries)")


def execute_command(args: argparse.Namespace) -> int:
    """
    Execute the appropriate command based on parsed arguments with comprehensive error handling.
    
    Args:
        args: Parsed arguments namespace
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    logger = logging.getLogger('v-and-r')
    
    try:
        # Validate VERSION_FILES configuration before proceeding
        logger.debug("Validating VERSION_FILES configuration")
        validate_version_files_config(VERSION_FILES)
        
        # Initialize CLI interface
        logger.debug("Initializing CLI interface")
        cli = CLIInterface()
        
        # Execute the requested command
        logger.info(f"Executing command with args: {args}")
        return cli.execute_command(args)
        
    except VAndRError as e:
        logger.error(f"Configuration error: {e}")
        print(f"Configuration Error: {e}", file=sys.stderr)
        print("\nPlease check your VERSION_FILES configuration and try again.", file=sys.stderr)
        return 2
        
    except VersionError as e:
        logger.error(f"Version error: {e}")
        print(f"Version Error: {e}", file=sys.stderr)
        print("\nPlease check your version formats and try again.", file=sys.stderr)
        return 3
        
    except FileError as e:
        logger.error(f"File error: {e}")
        print(f"File Error: {e}", file=sys.stderr)
        print("\nPlease check file permissions and paths, then try again.", file=sys.stderr)
        return 4
        
    except GitError as e:
        logger.error(f"Git error: {e}")
        print(f"Git Error: {e}", file=sys.stderr)
        print("\nPlease check your git repository status and try again.", file=sys.stderr)
        return 5
        
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user (Ctrl+C)")
        print("\nOperation cancelled by user.", file=sys.stderr)
        return 130
        
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        print(f"Unexpected Error: {e}", file=sys.stderr)
        print("\nThis is an unexpected error. Please report this issue with the following details:", file=sys.stderr)
        print(f"  - Command: {' '.join(sys.argv)}", file=sys.stderr)
        print(f"  - Error: {type(e).__name__}: {e}", file=sys.stderr)
        print(f"  - Python version: {sys.version}", file=sys.stderr)
        return 1


def main():
    """
    Main entry point for the v-and-r tool with comprehensive error handling and logging.
    
    This function orchestrates CLI parsing, command execution, and provides user-friendly
    error messages for different types of failures.
    """
    # Check for debug flag early to enable logging
    debug_mode = '--debug' in sys.argv or '-d' in sys.argv or os.getenv('V_AND_R_DEBUG', '').lower() in ('1', 'true', 'yes')
    
    # Set up logging
    setup_logging(debug=debug_mode)
    logger = logging.getLogger('v-and-r')
    
    logger.info("Starting v-and-r (Version and Release Manager)")
    logger.debug(f"Command line arguments: {sys.argv}")
    logger.debug(f"Python version: {sys.version}")
    logger.debug(f"Working directory: {os.getcwd()}")
    
    try:
        # Parse command line arguments
        logger.debug("Parsing command line arguments")
        cli = CLIInterface()
        args = cli.parse_arguments()
        
        logger.debug(f"Parsed arguments: {args}")
        
        # Execute the command
        exit_code = execute_command(args)
        
        logger.info(f"Command completed with exit code: {exit_code}")
        sys.exit(exit_code)
        
    except SystemExit as e:
        # Handle argparse exits (help, invalid args, etc.)
        logger.debug(f"SystemExit caught with code: {e.code}")
        sys.exit(e.code)
        
    except KeyboardInterrupt:
        logger.info("Main execution interrupted by user")
        print("\nOperation cancelled by user.", file=sys.stderr)
        sys.exit(130)
        
    except Exception as e:
        logger.exception(f"Fatal error in main: {e}")
        print(f"Fatal Error: {e}", file=sys.stderr)
        print("\nThe application encountered a fatal error and cannot continue.", file=sys.stderr)
        print("Please report this issue with the error details above.", file=sys.stderr)
        sys.exit(1)


# Integration Tests for Main Execution Flow
def test_main_execution_flow():
    """Integration tests for main execution flow and error handling"""
    import sys
    from unittest import mock
    from io import StringIO
    
    test_results = []
    
    def run_test(test_name: str, test_func):
        """Helper to run individual tests and track results"""
        try:
            test_func()
            test_results.append(f"✓ {test_name}")
            return True
        except Exception as e:
            test_results.append(f"✗ {test_name}: {e}")
            return False
    
    # Test VERSION_FILES validation
    def test_version_files_validation():
        # Test empty configuration
        try:
            validate_version_files_config([])
            assert False, "Should raise VAndRError for empty config"
        except VAndRError as e:
            assert "empty" in str(e).lower()
        
        # Test invalid configuration (missing keys)
        try:
            validate_version_files_config([{'file': 'test.py'}])
            assert False, "Should raise VAndRError for missing keys"
        except VAndRError as e:
            assert "missing required key" in str(e).lower()
        
        # Test invalid regex pattern
        try:
            validate_version_files_config([{
                'file': 'test.py',
                'pattern': 'not-a-regex-object',
                'template': 'version = "{version}"'
            }])
            assert False, "Should raise VAndRError for invalid pattern"
        except VAndRError as e:
            assert "compiled regex" in str(e).lower()
        
        # Test valid configuration
        valid_config = [{
            'file': 'test.py',
            'pattern': re.compile(r'version = "(v\d+\.\d+\.\d+)"'),
            'template': 'version = "{version}"'
        }]
        validate_version_files_config(valid_config)  # Should not raise
    
    # Test logging setup
    def test_logging_setup():
        # Test debug logging setup
        setup_logging(debug=True)
        logger = logging.getLogger('v-and-r')
        assert logger.level == logging.DEBUG
        
        # Test normal logging setup
        setup_logging(debug=False)
        logger = logging.getLogger('v-and-r')
        assert logger.level == logging.INFO
    
    # Test main execution with mocked arguments
    def test_main_execution_with_mocked_args():
        with mock.patch('sys.argv', ['v-and-r', '--view']):
            with mock.patch.object(CLIInterface, 'execute_command', return_value=0) as mock_execute:
                exit_code = execute_command(argparse.Namespace(view=True, debug=False))
                assert exit_code == 0
                mock_execute.assert_called_once()
    
    # Test error handling in execute_command
    def test_execute_command_error_handling():
        # Test VAndRError handling - need to mock the CLI creation to raise the error
        with mock.patch('__main__.CLIInterface', side_effect=VAndRError("Test error")):
            exit_code = execute_command(argparse.Namespace(view=True, debug=False))
            assert exit_code == 2
        
        # Test VersionError handling
        with mock.patch('__main__.CLIInterface', side_effect=VersionError("Test version error")):
            exit_code = execute_command(argparse.Namespace(view=True, debug=False))
            assert exit_code == 3
        
        # Test FileError handling
        with mock.patch('__main__.CLIInterface', side_effect=FileError("Test file error")):
            exit_code = execute_command(argparse.Namespace(view=True, debug=False))
            assert exit_code == 4
        
        # Test GitError handling
        with mock.patch('__main__.CLIInterface', side_effect=GitError("Test git error")):
            exit_code = execute_command(argparse.Namespace(view=True, debug=False))
            assert exit_code == 5
        
        # Test unexpected error handling
        with mock.patch('__main__.CLIInterface', side_effect=RuntimeError("Unexpected error")):
            exit_code = execute_command(argparse.Namespace(view=True, debug=False))
            assert exit_code == 1
    
    # Run all tests
    print("\nRunning Main Execution Flow integration tests...")
    print("=" * 50)
    
    tests = [
        ("VERSION_FILES validation", test_version_files_validation),
        ("logging setup", test_logging_setup),
        ("main execution with mocked args", test_main_execution_with_mocked_args),
        ("execute_command error handling", test_execute_command_error_handling),
    ]
    
    passed = 0
    for test_name, test_func in tests:
        if run_test(test_name, test_func):
            passed += 1
    
    # Print results
    for result in test_results:
        print(result)
    
    print("=" * 50)
    print(f"Tests passed: {passed}/{len(tests)}")
    
    if passed == len(tests):
        print("All Main Execution Flow tests passed! ✓")
        return True
    else:
        print("Some tests failed! ✗")
        return False


# Unit Tests for CLIInterface
def test_cli_interface():
    """Comprehensive unit tests for CLIInterface class"""
    import sys
    from unittest import mock
    from io import StringIO
    
    test_results = []
    
    def run_test(test_name: str, test_func):
        """Helper to run individual tests and track results"""
        try:
            test_func()
            test_results.append(f"✓ {test_name}")
            return True
        except Exception as e:
            test_results.append(f"✗ {test_name}: {e}")
            return False
    
    # Test argument parsing
    def test_parse_arguments():
        cli = CLIInterface()
        
        # Test default behavior (no arguments should default to view)
        with mock.patch('sys.argv', ['v-and-r']):
            args = cli.parse_arguments()
            assert args.view == True
        
        # Test view command
        with mock.patch('sys.argv', ['v-and-r', '-v']):
            args = cli.parse_arguments()
            assert args.view == True
        
        with mock.patch('sys.argv', ['v-and-r', '--view']):
            args = cli.parse_arguments()
            assert args.view == True
        
        # Test patch command
        with mock.patch('sys.argv', ['v-and-r', '-p']):
            args = cli.parse_arguments()
            assert args.patch == True
        
        with mock.patch('sys.argv', ['v-and-r', '--patch']):
            args = cli.parse_arguments()
            assert args.patch == True
        
        # Test minor command
        with mock.patch('sys.argv', ['v-and-r', '-mi']):
            args = cli.parse_arguments()
            assert args.minor == True
        
        with mock.patch('sys.argv', ['v-and-r', '--minor']):
            args = cli.parse_arguments()
            assert args.minor == True
        
        # Test major command
        with mock.patch('sys.argv', ['v-and-r', '-ma']):
            args = cli.parse_arguments()
            assert args.major == True
        
        with mock.patch('sys.argv', ['v-and-r', '--major']):
            args = cli.parse_arguments()
            assert args.major == True
        
        # Test release info command
        with mock.patch('sys.argv', ['v-and-r', '-r']):
            args = cli.parse_arguments()
            assert args.release_info == True
        
        with mock.patch('sys.argv', ['v-and-r', '--release-info']):
            args = cli.parse_arguments()
            assert args.release_info == True
        
        # Test release diff command
        with mock.patch('sys.argv', ['v-and-r', '-rd', 'v1.0.0', 'v1.1.0']):
            args = cli.parse_arguments()
            assert args.release_diff == ['v1.0.0', 'v1.1.0']
        
        with mock.patch('sys.argv', ['v-and-r', '--release-diff', 'v1.0.0', 'v1.1.0']):
            args = cli.parse_arguments()
            assert args.release_diff == ['v1.0.0', 'v1.1.0']
        
        # Test release last command
        with mock.patch('sys.argv', ['v-and-r', '-rl']):
            args = cli.parse_arguments()
            assert args.release_last == True
        
        with mock.patch('sys.argv', ['v-and-r', '--release-last']):
            args = cli.parse_arguments()
            assert args.release_last == True
        
        # Test release prepare command
        with mock.patch('sys.argv', ['v-and-r', '-rp']):
            args = cli.parse_arguments()
            assert args.release_prepare == True
        
        with mock.patch('sys.argv', ['v-and-r', '--release-prepare']):
            args = cli.parse_arguments()
            assert args.release_prepare == True
    
    def test_argument_validation():
        cli = CLIInterface()
        
        # Test release-diff with same tags (should exit with error)
        with mock.patch('sys.argv', ['v-and-r', '-rd', 'v1.0.0', 'v1.0.0']):
            with mock.patch('sys.exit') as mock_exit:
                cli.parse_arguments()
                mock_exit.assert_called_with(1)
        
        # Test mutually exclusive arguments (should work - argparse handles this)
        # We can't easily test this without triggering SystemExit, so we'll skip detailed testing
        # The argparse library handles mutual exclusion automatically
    
    def test_execute_view_command():
        cli = CLIInterface()
        
        # Mock file manager to return versions
        mock_versions = {
            'app.py': 'v1.2.3',
            'README.md': 'v1.2.3'
        }
        
        with mock.patch.object(cli.file_manager, 'find_versions_in_files', return_value=mock_versions):
            with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                result = cli._execute_view_command()
                assert result == 0
                output = mock_stdout.getvalue()
                assert 'app.py: v1.2.3' in output
                assert 'README.md: v1.2.3' in output
    
    def test_generate_release_info():
        cli = CLIInterface()
        
        # Mock file manager to return versions
        mock_versions = {'app.py': 'v1.2.3'}
        
        with mock.patch.object(cli.file_manager, 'find_versions_in_files', return_value=mock_versions):
            with mock.patch.object(cli.git_manager, 'is_git_repository', return_value=True):
                with mock.patch.object(cli.git_manager, 'get_current_commit_hash', return_value='abc1234'):
                    with mock.patch.object(cli.git_manager, 'get_git_tags', return_value=['v1.1.0', 'v1.0.0']):
                        with mock.patch.object(cli.git_manager, 'get_commits_since_tag', return_value=[
                            {'hash': 'abc1234', 'message': 'feat: add new feature', 'author': 'Test User', 'date': '2023-01-01'}
                        ]):
                            release_info = cli.generate_release_info()
                            
                            assert release_info.version == 'v1.2.3'
                            assert release_info.commit_hash == 'abc1234'
                            assert release_info.previous_version == 'v1.1.0'
                            assert len(release_info.commits) == 1
                            assert release_info.commits[0]['message'] == 'feat: add new feature'
    
    def test_generate_release_info_no_git():
        cli = CLIInterface()
        
        # Mock file manager to return versions
        mock_versions = {'app.py': 'v1.2.3'}
        
        with mock.patch.object(cli.file_manager, 'find_versions_in_files', return_value=mock_versions):
            with mock.patch.object(cli.git_manager, 'is_git_repository', return_value=False):
                release_info = cli.generate_release_info()
                
                assert release_info.version == 'v1.2.3'
                assert release_info.commit_hash == 'unknown'
                assert release_info.previous_version is None
                assert len(release_info.commits) == 0
    
    def test_generate_release_info_git_errors():
        cli = CLIInterface()
        
        # Mock file manager to return versions
        mock_versions = {'app.py': 'v1.2.3'}
        
        with mock.patch.object(cli.file_manager, 'find_versions_in_files', return_value=mock_versions):
            with mock.patch.object(cli.git_manager, 'is_git_repository', return_value=True):
                with mock.patch.object(cli.git_manager, 'get_current_commit_hash', side_effect=GitError("Git failed")):
                    release_info = cli.generate_release_info()
                    
                    assert release_info.version == 'v1.2.3'
                    assert release_info.commit_hash == 'unknown'
                    assert len(release_info.commits) == 0
    
    def test_format_release_notes():
        cli = CLIInterface()
        
        commits = [
            {'hash': 'abc1234567', 'message': 'feat: add new feature', 'author': 'Test User', 'date': '2023-01-01'},
            {'hash': 'def5678901', 'message': 'fix: resolve bug', 'author': 'Test User', 'date': '2023-01-02'},
            {'hash': 'ghi2345678', 'message': 'docs: update readme', 'author': 'Test User', 'date': '2023-01-03'},
            {'hash': 'jkl9012345', 'message': 'refactor: improve code', 'author': 'Test User', 'date': '2023-01-04'}
        ]
        
        with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            cli._format_release_notes(commits)
            output = mock_stdout.getvalue()
            
            assert "Features:" in output
            assert "feat: add new feature (abc1234)" in output
            assert "Bug Fixes:" in output
            assert "fix: resolve bug (def5678)" in output
            assert "Documentation:" in output
            assert "docs: update readme (ghi2345)" in output
            assert "Other:" in output
            assert "refactor: improve code (jkl9012)" in output
            assert "Total commits: 4" in output
        
        # Test no versions found
        with mock.patch.object(cli.file_manager, 'find_versions_in_files', return_value={}):
            with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                result = cli._execute_view_command()
                assert result == 0
                output = mock_stdout.getvalue()
                assert 'No versions found' in output
        
        # Test file error
        with mock.patch.object(cli.file_manager, 'find_versions_in_files', side_effect=FileError("Test error")):
            with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                result = cli._execute_view_command()
                assert result == 1
                output = mock_stdout.getvalue()
                assert 'File error: Test error' in output
    
    def test_execute_increment_command():
        cli = CLIInterface()
        
        # Mock successful increment with user confirmation
        mock_versions = {'app.py': 'v1.2.3'}
        mock_expanded_files = ['app.py']
        
        with mock.patch.object(cli.file_manager, 'find_versions_in_files', return_value=mock_versions):
            with mock.patch.object(cli.file_manager, 'expand_file_patterns', return_value=mock_expanded_files):
                with mock.patch.object(cli.file_manager, 'update_file_version', return_value=True):
                    with mock.patch('builtins.input', return_value='y'):  # User confirms
                        with mock.patch('builtins.open', mock.mock_open(read_data='version = "v1.2.3"')):
                            with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                                result = cli._execute_increment_command('patch')
                                assert result == 0
                                output = mock_stdout.getvalue()
                                assert 'v1.2.3' in output
                                assert 'v1.2.4' in output
                                assert '✓ app.py' in output
                                assert 'Successfully updated' in output
        
        # Test user cancellation
        with mock.patch.object(cli.file_manager, 'find_versions_in_files', return_value=mock_versions):
            with mock.patch('builtins.input', return_value='n'):  # User cancels
                with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                    result = cli._execute_increment_command('patch')
                    assert result == 0
                    output = mock_stdout.getvalue()
                    assert 'Operation cancelled' in output
        
        # Test no versions found
        with mock.patch.object(cli.file_manager, 'find_versions_in_files', return_value={}):
            with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                result = cli._execute_increment_command('patch')
                assert result == 1
                output = mock_stdout.getvalue()
                assert 'No versions found' in output
        
        # Test file update failure with rollback
        with mock.patch.object(cli.file_manager, 'find_versions_in_files', return_value=mock_versions):
            with mock.patch.object(cli.file_manager, 'expand_file_patterns', return_value=mock_expanded_files):
                with mock.patch.object(cli.file_manager, 'update_file_version', side_effect=FileError("Write failed")):
                    with mock.patch('builtins.input', side_effect=['y', 'y']):  # Confirm update, then rollback
                        with mock.patch('builtins.open', mock.mock_open(read_data='version = "v1.2.3"')):
                            with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                                result = cli._execute_increment_command('minor')
                                assert result == 1
                                output = mock_stdout.getvalue()
                                assert 'failed' in output
                                assert 'Rolling back' in output
        
        # Test KeyboardInterrupt during confirmation
        with mock.patch.object(cli.file_manager, 'find_versions_in_files', return_value=mock_versions):
            with mock.patch('builtins.input', side_effect=KeyboardInterrupt()):
                with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                    result = cli._execute_increment_command('major')
                    assert result == 0
                    output = mock_stdout.getvalue()
                    assert 'Operation cancelled' in output
    
    def test_rollback_mechanism():
        cli = CLIInterface()
        
        # Test successful rollback
        original_contents = {
            'app.py': 'version = "v1.2.3"',
            'config.py': 'VERSION = "v1.2.3"'
        }
        update_results = {
            'app.py': True,
            'config.py': True
        }
        
        with mock.patch('builtins.open', mock.mock_open()) as mock_file:
            with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                cli._rollback_file_changes(original_contents, update_results)
                output = mock_stdout.getvalue()
                assert 'Rolled back app.py' in output
                assert 'Rolled back config.py' in output
                assert 'Successfully rolled back 2 files' in output
        
        # Test rollback with some failures
        with mock.patch('builtins.open', side_effect=[IOError("Permission denied"), mock.mock_open().return_value]):
            with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                cli._rollback_file_changes(original_contents, update_results)
                output = mock_stdout.getvalue()
                assert 'Failed to rollback app.py' in output
                assert 'Rolled back config.py' in output
                assert 'could not be rolled back' in output
    
    def test_increment_integration():
        """Integration test for complete increment workflow"""
        cli = CLIInterface()
        
        # Test patch increment integration
        mock_versions = {'test.py': 'v1.2.3', 'config.py': 'v1.2.2'}
        mock_expanded_files = ['test.py', 'config.py']
        
        with mock.patch.object(cli.file_manager, 'find_versions_in_files', return_value=mock_versions):
            with mock.patch.object(cli.file_manager, 'expand_file_patterns', return_value=mock_expanded_files):
                with mock.patch.object(cli.file_manager, 'update_file_version', return_value=True):
                    with mock.patch('builtins.input', return_value='yes'):
                        with mock.patch('builtins.open', mock.mock_open(read_data='version = "v1.2.3"')):
                            with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                                result = cli._execute_increment_command('patch')
                                assert result == 0
                                output = mock_stdout.getvalue()
                                # Should find highest version v1.2.3 and increment to v1.2.4
                                assert 'v1.2.3' in output
                                assert 'v1.2.4' in output
                                assert 'Successfully updated 2 files' in output
        
        # Test minor increment integration
        with mock.patch.object(cli.file_manager, 'find_versions_in_files', return_value=mock_versions):
            with mock.patch.object(cli.file_manager, 'expand_file_patterns', return_value=mock_expanded_files):
                with mock.patch.object(cli.file_manager, 'update_file_version', return_value=True):
                    with mock.patch('builtins.input', return_value='y'):
                        with mock.patch('builtins.open', mock.mock_open(read_data='version = "v1.2.3"')):
                            with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                                result = cli._execute_increment_command('minor')
                                assert result == 0
                                output = mock_stdout.getvalue()
                                # Should find highest version v1.2.3 and increment to v1.3.0
                                assert 'v1.2.3' in output
                                assert 'v1.3.0' in output
        
        # Test major increment integration
        with mock.patch.object(cli.file_manager, 'find_versions_in_files', return_value=mock_versions):
            with mock.patch.object(cli.file_manager, 'expand_file_patterns', return_value=mock_expanded_files):
                with mock.patch.object(cli.file_manager, 'update_file_version', return_value=True):
                    with mock.patch('builtins.input', return_value='y'):
                        with mock.patch('builtins.open', mock.mock_open(read_data='version = "v1.2.3"')):
                            with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                                result = cli._execute_increment_command('major')
                                assert result == 0
                                output = mock_stdout.getvalue()
                                # Should find highest version v1.2.3 and increment to v2.0.0
                                assert 'v1.2.3' in output
                                assert 'v2.0.0' in output
    
    def test_execute_release_diff_command():
        cli = CLIInterface()
        
        # Test successful release diff
        mock_commits = [
            {'hash': 'abc1234567', 'message': 'feat: add new feature', 'author': 'Test User', 'date': '2023-01-01T10:00:00'},
            {'hash': 'def5678901', 'message': 'fix: resolve bug', 'author': 'Test User', 'date': '2023-01-02T10:00:00'}
        ]
        
        with mock.patch.object(cli.git_manager, 'is_git_repository', return_value=True):
            with mock.patch.object(cli.git_manager, 'get_git_tags', return_value=['v1.1.0', 'v1.0.0']):
                with mock.patch.object(cli.git_manager, 'get_commits_between_tags', return_value=mock_commits):
                    with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                        result = cli._execute_release_diff_command('v1.0.0', 'v1.1.0')
                        assert result == 0
                        output = mock_stdout.getvalue()
                        assert 'Commits between v1.0.0 and v1.1.0' in output
                        assert 'Found 2 commits' in output
                        assert 'abc1234' in output
                        assert 'feat: add new feature' in output
        
        # Test not in git repository
        with mock.patch.object(cli.git_manager, 'is_git_repository', return_value=False):
            with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                result = cli._execute_release_diff_command('v1.0.0', 'v1.1.0')
                assert result == 1
                output = mock_stdout.getvalue()
                assert 'Not in a git repository' in output
        
        # Test invalid tag
        with mock.patch.object(cli.git_manager, 'is_git_repository', return_value=True):
            with mock.patch.object(cli.git_manager, 'get_git_tags', return_value=['v1.1.0', 'v1.0.0']):
                with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                    result = cli._execute_release_diff_command('v2.0.0', 'v1.1.0')
                    assert result == 1
                    output = mock_stdout.getvalue()
                    assert "Tag 'v2.0.0' does not exist" in output
                    assert 'Available tags:' in output
        
        # Test no commits between tags
        with mock.patch.object(cli.git_manager, 'is_git_repository', return_value=True):
            with mock.patch.object(cli.git_manager, 'get_git_tags', return_value=['v1.1.0', 'v1.0.0']):
                with mock.patch.object(cli.git_manager, 'get_commits_between_tags', return_value=[]):
                    with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                        result = cli._execute_release_diff_command('v1.0.0', 'v1.1.0')
                        assert result == 0
                        output = mock_stdout.getvalue()
                        assert 'No commits found between' in output
        
        # Test git error
        with mock.patch.object(cli.git_manager, 'is_git_repository', return_value=True):
            with mock.patch.object(cli.git_manager, 'get_git_tags', side_effect=GitError("Git failed")):
                with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                    result = cli._execute_release_diff_command('v1.0.0', 'v1.1.0')
                    assert result == 1
                    output = mock_stdout.getvalue()
                    assert 'Error retrieving git tags' in output
    
    def test_execute_release_last_command():
        cli = CLIInterface()
        
        # Test successful release last with existing tag
        mock_commits = [
            {'hash': 'abc1234567', 'message': 'feat: add new feature', 'author': 'Test User', 'date': '2023-01-01T10:00:00'},
            {'hash': 'def5678901', 'message': 'fix: resolve bug', 'author': 'Test User', 'date': '2023-01-02T10:00:00'}
        ]
        
        with mock.patch.object(cli.git_manager, 'is_git_repository', return_value=True):
            with mock.patch.object(cli.git_manager, 'get_latest_tag', return_value='v1.0.0'):
                with mock.patch.object(cli.git_manager, 'get_commits_since_tag', return_value=mock_commits):
                    with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                        result = cli._execute_release_last_command()
                        assert result == 0
                        output = mock_stdout.getvalue()
                        assert 'Latest tag: v1.0.0' in output
                        assert 'Found 2 commits since v1.0.0' in output
                        assert 'abc1234' in output
        
        # Test no commits since last tag
        with mock.patch.object(cli.git_manager, 'is_git_repository', return_value=True):
            with mock.patch.object(cli.git_manager, 'get_latest_tag', return_value='v1.0.0'):
                with mock.patch.object(cli.git_manager, 'get_commits_since_tag', return_value=[]):
                    with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                        result = cli._execute_release_last_command()
                        assert result == 0
                        output = mock_stdout.getvalue()
                        assert 'No commits found since v1.0.0' in output
                        assert 'up to date' in output
        
        # Test no tags exist - show all commits
        with mock.patch.object(cli.git_manager, 'is_git_repository', return_value=True):
            with mock.patch.object(cli.git_manager, 'get_latest_tag', side_effect=GitError("No tags found")):
                with mock.patch.object(cli.git_manager, 'get_all_commits_since_beginning', return_value=mock_commits):
                    with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                        result = cli._execute_release_last_command()
                        assert result == 0
                        output = mock_stdout.getvalue()
                        assert 'No git tags found' in output
                        assert 'showing all commits from repository beginning' in output
                        assert 'Found 2 total commits' in output
        
        # Test not in git repository
        with mock.patch.object(cli.git_manager, 'is_git_repository', return_value=False):
            with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                result = cli._execute_release_last_command()
                assert result == 1
                output = mock_stdout.getvalue()
                assert 'Not in a git repository' in output
        
        # Test no commits in repository
        with mock.patch.object(cli.git_manager, 'is_git_repository', return_value=True):
            with mock.patch.object(cli.git_manager, 'get_latest_tag', side_effect=GitError("No tags found")):
                with mock.patch.object(cli.git_manager, 'get_all_commits_since_beginning', return_value=[]):
                    with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                        result = cli._execute_release_last_command()
                        assert result == 0
                        output = mock_stdout.getvalue()
                        assert 'No commits found in this repository' in output
    
    def test_format_commit_history():
        cli = CLIInterface()
        
        # Test formatting with multiple commits
        commits = [
            {'hash': 'abc1234567890', 'message': 'feat: add new feature', 'author': 'Alice', 'date': '2023-01-01T10:00:00'},
            {'hash': 'def5678901234', 'message': 'fix: resolve bug', 'author': 'Bob', 'date': '2023-01-02T10:00:00'},
            {'hash': 'ghi9012345678', 'message': 'docs: update readme', 'author': 'Alice', 'date': '2023-01-03T10:00:00'}
        ]
        
        with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            cli._format_commit_history(commits, show_stats=True)
            output = mock_stdout.getvalue()
            
            # Check commit display
            assert 'abc1234  feat: add new feature' in output
            assert 'Author: Alice' in output
            assert 'Date: 2023-01-01' in output
            assert 'def5678  fix: resolve bug' in output
            assert 'Author: Bob' in output
            
            # Check statistics
            assert 'Total commits: 3' in output
            assert 'Contributors: 2' in output
            assert 'Alice, Bob' in output
            assert 'Date range: 2023-01-01 to 2023-01-03' in output
            assert 'Breakdown:' in output
            assert '1 features' in output
            assert '1 bug fixes' in output
            assert '1 documentation' in output
        
        # Test with no commits
        with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            cli._format_commit_history([], show_stats=True)
            output = mock_stdout.getvalue()
            assert 'No commits to display' in output
        
        # Test without statistics
        with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            cli._format_commit_history(commits[:1], show_stats=False)
            output = mock_stdout.getvalue()
            assert 'abc1234  feat: add new feature' in output
            assert 'Total commits:' not in output
    
    def test_execute_command_routing():
        cli = CLIInterface()
        
        # Create mock args for different commands
        mock_args_view = argparse.Namespace(
            view=True, patch=False, minor=False, major=False,
            release_info=False, release_diff=None, release_last=False,
            release_prepare=False
        )
        
        mock_args_patch = argparse.Namespace(
            view=False, patch=True, minor=False, major=False,
            release_info=False, release_diff=None, release_last=False,
            release_prepare=False
        )
        
        mock_args_release_diff = argparse.Namespace(
            view=False, patch=False, minor=False, major=False,
            release_info=False, release_diff=['v1.0.0', 'v1.1.0'], release_last=False,
            release_prepare=False
        )
        
        mock_args_release_last = argparse.Namespace(
            view=False, patch=False, minor=False, major=False,
            release_info=False, release_diff=None, release_last=True,
            release_prepare=False
        )
        
        # Test view command routing
        with mock.patch.object(cli, '_execute_view_command', return_value=0) as mock_view:
            result = cli.execute_command(mock_args_view)
            assert result == 0
            mock_view.assert_called_once()
        
        # Test patch command routing
        with mock.patch.object(cli, '_execute_increment_command', return_value=0) as mock_increment:
            result = cli.execute_command(mock_args_patch)
            assert result == 0
            mock_increment.assert_called_once_with('patch')
        
        # Test release diff command routing
        with mock.patch.object(cli, '_execute_release_diff_command', return_value=0) as mock_diff:
            result = cli.execute_command(mock_args_release_diff)
            assert result == 0
            mock_diff.assert_called_once_with('v1.0.0', 'v1.1.0')
        
        # Test release last command routing
        with mock.patch.object(cli, '_execute_release_last_command', return_value=0) as mock_last:
            result = cli.execute_command(mock_args_release_last)
            assert result == 0
            mock_last.assert_called_once()
        
        # Test error handling
        with mock.patch.object(cli, '_execute_view_command', side_effect=VersionError("Test error")):
            with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                result = cli.execute_command(mock_args_view)
                assert result == 1
                output = mock_stdout.getvalue()
                assert 'Error: Test error' in output
        
        # Test keyboard interrupt
        with mock.patch.object(cli, '_execute_view_command', side_effect=KeyboardInterrupt()):
            with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                result = cli.execute_command(mock_args_view)
                assert result == 130
                output = mock_stdout.getvalue()
                assert 'Operation cancelled' in output
        
        # Test unexpected error
        with mock.patch.object(cli, '_execute_view_command', side_effect=RuntimeError("Unexpected")):
            with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                result = cli.execute_command(mock_args_view)
                assert result == 1
                output = mock_stdout.getvalue()
                assert 'Unexpected error' in output
    
    def test_execute_release_prepare_command():
        cli = CLIInterface()
        
        # Mock release info
        mock_release_info = ReleaseInfo(
            version="v1.2.3",
            timestamp="2023-01-01T10:00:00",
            commit_hash="abc1234",
            commits=[
                {'hash': 'abc1234567', 'message': 'feat: add new feature', 'author': 'Test User', 'date': '2023-01-01T10:00:00'},
                {'hash': 'def5678901', 'message': 'fix: resolve bug', 'author': 'Test User', 'date': '2023-01-02T10:00:00'}
            ],
            previous_version="v1.2.2"
        )
        
        # Test successful release preparation
        with mock.patch.object(cli, 'generate_release_info', return_value=mock_release_info):
            with mock.patch.object(cli, '_update_version_json') as mock_version_json:
                with mock.patch.object(cli, '_update_changelog') as mock_changelog:
                    with mock.patch.object(cli, '_update_releases') as mock_releases:
                        with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                            result = cli._execute_release_prepare_command()
                            assert result == 0
                            output = mock_stdout.getvalue()
                            assert 'Preparing release documentation' in output
                            assert 'Release preparation completed successfully!' in output
                            assert 'v1.2.3' in output
                            assert 'version.json, CHANGELOG.md, RELEASES.md' in output
                            assert 'Commits included: 2' in output
                            
                            # Verify all update methods were called
                            mock_version_json.assert_called_once_with(mock_release_info)
                            mock_changelog.assert_called_once_with(mock_release_info)
                            mock_releases.assert_called_once_with(mock_release_info)
        
        # Test error during release info generation
        with mock.patch.object(cli, 'generate_release_info', side_effect=VAndRError("Cannot determine version")):
            with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                result = cli._execute_release_prepare_command()
                assert result == 1
                output = mock_stdout.getvalue()
                assert 'Error preparing release: Cannot determine version' in output
        
        # Test error during file updates
        with mock.patch.object(cli, 'generate_release_info', return_value=mock_release_info):
            with mock.patch.object(cli, '_update_version_json', side_effect=FileError("Cannot write file")):
                with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                    result = cli._execute_release_prepare_command()
                    assert result == 1
                    output = mock_stdout.getvalue()
                    assert 'Error preparing release: Cannot write file' in output
        
        # Test unexpected error
        with mock.patch.object(cli, 'generate_release_info', side_effect=RuntimeError("Unexpected error")):
            with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                result = cli._execute_release_prepare_command()
                assert result == 1
                output = mock_stdout.getvalue()
                assert 'Unexpected error during release preparation: Unexpected error' in output
    
    def test_update_version_json():
        cli = CLIInterface()
        
        mock_release_info = ReleaseInfo(
            version="v1.2.3",
            timestamp="2023-01-01T10:00:00",
            commit_hash="abc1234",
            commits=[],
            previous_version="v1.2.2"
        )
        
        # Test successful version.json update
        with mock.patch('builtins.open', mock.mock_open()) as mock_file:
            with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                cli._update_version_json(mock_release_info)
                output = mock_stdout.getvalue()
                assert '✓ version.json updated successfully' in output
                
                # Verify file was opened for writing
                mock_file.assert_called_once_with('version.json', 'w', encoding='utf-8')
                
                # Verify JSON content was written
                handle = mock_file()
                written_content = ''.join(call.args[0] for call in handle.write.call_args_list)
                assert '"version": "v1.2.3"' in written_content
                assert '"timestamp": "2023-01-01T10:00:00"' in written_content
        
        # Test file write error
        with mock.patch('builtins.open', side_effect=IOError("Permission denied")):
            try:
                cli._update_version_json(mock_release_info)
                assert False, "Should raise FileError"
            except FileError as e:
                assert "Cannot write version.json: Permission denied" in str(e)
    
    def test_update_changelog():
        cli = CLIInterface()
        
        mock_release_info = ReleaseInfo(
            version="v1.2.3",
            timestamp="2023-01-01T10:00:00",
            commit_hash="abc1234",
            commits=[
                {'hash': 'abc1234567', 'message': 'feat: add new feature', 'author': 'Test User', 'date': '2023-01-01T10:00:00'},
                {'hash': 'def5678901', 'message': 'fix: resolve bug', 'author': 'Test User', 'date': '2023-01-02T10:00:00'}
            ],
            previous_version="v1.2.2"
        )
        
        # Test creating new CHANGELOG.md
        with mock.patch('os.path.exists', return_value=False):
            with mock.patch('builtins.open', mock.mock_open()) as mock_file:
                with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                    cli._update_changelog(mock_release_info)
                    output = mock_stdout.getvalue()
                    assert '✓ CHANGELOG.md updated successfully' in output
                    
                    # Verify file was written
                    mock_file.assert_called_with('CHANGELOG.md', 'w', encoding='utf-8')
                    handle = mock_file()
                    written_content = ''.join(call.args[0] for call in handle.write.call_args_list)
                    assert '# Changelog' in written_content
                    assert '[v1.2.3]' in written_content
                    assert 'add new feature' in written_content
        
        # Test updating existing CHANGELOG.md
        existing_changelog = """# Changelog
All notable changes to this project will be documented here.

## [Unreleased]

## [v1.2.2] - 2022-12-01
### Fixed
- Previous bug fix
"""
        
        with mock.patch('os.path.exists', return_value=True):
            with mock.patch('builtins.open', mock.mock_open(read_data=existing_changelog)) as mock_file:
                with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                    cli._update_changelog(mock_release_info)
                    output = mock_stdout.getvalue()
                    assert '✓ CHANGELOG.md updated successfully' in output
                    
                    # Verify new entry was inserted before existing entries
                    handle = mock_file()
                    written_content = ''.join(call.args[0] for call in handle.write.call_args_list)
                    assert '[v1.2.3]' in written_content
                    assert '[v1.2.2]' in written_content
                    # New version should appear before old version
                    v123_pos = written_content.find('[v1.2.3]')
                    v122_pos = written_content.find('[v1.2.2]')
                    assert v123_pos < v122_pos
        
        # Test file read error
        with mock.patch('os.path.exists', return_value=True):
            with mock.patch('builtins.open', side_effect=IOError("Cannot read file")):
                try:
                    cli._update_changelog(mock_release_info)
                    assert False, "Should raise FileError"
                except FileError as e:
                    assert "Cannot read existing CHANGELOG.md" in str(e)
    
    def test_update_releases():
        cli = CLIInterface()
        
        mock_release_info = ReleaseInfo(
            version="v1.2.3",
            timestamp="2023-01-01T10:00:00",
            commit_hash="abc1234",
            commits=[
                {'hash': 'abc1234567', 'message': 'feat: add new feature', 'author': 'Alice', 'date': '2023-01-01T10:00:00'},
                {'hash': 'def5678901', 'message': 'fix: resolve bug', 'author': 'Bob', 'date': '2023-01-02T10:00:00'}
            ],
            previous_version="v1.2.2"
        )
        
        # Test creating new RELEASES.md
        with mock.patch('os.path.exists', return_value=False):
            with mock.patch('builtins.open', mock.mock_open()) as mock_file:
                with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                    cli._update_releases(mock_release_info)
                    output = mock_stdout.getvalue()
                    assert '✓ RELEASES.md updated successfully' in output
                    
                    # Verify file was written
                    mock_file.assert_called_with('RELEASES.md', 'w', encoding='utf-8')
                    handle = mock_file()
                    written_content = ''.join(call.args[0] for call in handle.write.call_args_list)
                    assert '# Releases' in written_content
                    assert '## v1.2.3' in written_content
                    assert '2 commits' in written_content
                    assert '2 contributors' in written_content
                    assert 'Alice, Bob' in written_content
        
        # Test updating existing RELEASES.md
        existing_releases = """# Releases

This document contains release notes and highlights for each version.

## v1.2.2 - 2022-12-01

Previous release notes.
"""
        
        with mock.patch('os.path.exists', return_value=True):
            with mock.patch('builtins.open', mock.mock_open(read_data=existing_releases)) as mock_file:
                with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                    cli._update_releases(mock_release_info)
                    output = mock_stdout.getvalue()
                    assert '✓ RELEASES.md updated successfully' in output
                    
                    # Verify new entry was inserted before existing entries
                    handle = mock_file()
                    written_content = ''.join(call.args[0] for call in handle.write.call_args_list)
                    assert '## v1.2.3' in written_content
                    assert '## v1.2.2' in written_content
                    # New version should appear before old version
                    v123_pos = written_content.find('## v1.2.3')
                    v122_pos = written_content.find('## v1.2.2')
                    assert v123_pos < v122_pos
    
    def test_generate_changelog_entry():
        cli = CLIInterface()
        
        # Test with commits
        mock_release_info = ReleaseInfo(
            version="v1.2.3",
            timestamp="2023-01-01T10:00:00",
            commit_hash="abc1234",
            commits=[
                {'hash': 'abc1234567', 'message': 'feat: add new feature', 'author': 'Alice', 'date': '2023-01-01T10:00:00'},
                {'hash': 'def5678901', 'message': 'fix: resolve bug', 'author': 'Bob', 'date': '2023-01-02T10:00:00'},
                {'hash': 'ghi9012345', 'message': 'docs: update readme', 'author': 'Alice', 'date': '2023-01-03T10:00:00'}
            ],
            previous_version="v1.2.2"
        )
        
        entry = cli._generate_changelog_entry(mock_release_info)
        
        assert '## [v1.2.3] - 2023-01-01' in entry
        assert '### Added' in entry
        assert 'add new feature' in entry
        assert '### Fixed' in entry
        assert 'resolve bug' in entry
        assert '### Changed' in entry
        assert 'Documentation: update readme' in entry
        assert '### Commits' in entry
        assert 'abc1234' in entry
        
        # Test with no commits
        mock_release_info_no_commits = ReleaseInfo(
            version="v1.2.3",
            timestamp="2023-01-01T10:00:00",
            commit_hash="abc1234",
            commits=[],
            previous_version="v1.2.2"
        )
        
        entry_no_commits = cli._generate_changelog_entry(mock_release_info_no_commits)
        assert '## [v1.2.3] - 2023-01-01' in entry_no_commits
        assert 'Version bump to v1.2.3' in entry_no_commits
    
    def test_generate_releases_entry():
        cli = CLIInterface()
        
        # Test with commits
        mock_release_info = ReleaseInfo(
            version="v1.2.3",
            timestamp="2023-01-01T10:00:00",
            commit_hash="abc1234",
            commits=[
                {'hash': 'abc1234567', 'message': 'feat: add new feature', 'author': 'Alice', 'date': '2023-01-01T10:00:00'},
                {'hash': 'def5678901', 'message': 'fix: resolve bug', 'author': 'Bob', 'date': '2023-01-02T10:00:00'}
            ],
            previous_version="v1.2.2"
        )
        
        entry = cli._generate_releases_entry(mock_release_info)
        
        assert '## v1.2.3 - 2023-01-01' in entry
        assert '**2 commits** from **2 contributors**' in entry
        assert 'Changes since v1.2.2:' in entry
        assert '1 new features, 1 bug fixes' in entry
        assert '**Contributors:** Alice, Bob' in entry
        assert '**Commit Hash:** `abc1234`' in entry
        assert 'add new feature' in entry
        assert 'resolve bug' in entry
        
        # Test with no commits
        mock_release_info_no_commits = ReleaseInfo(
            version="v1.2.3",
            timestamp="2023-01-01T10:00:00",
            commit_hash="abc1234",
            commits=[],
            previous_version="v1.2.2"
        )
        
        entry_no_commits = cli._generate_releases_entry(mock_release_info_no_commits)
        assert '## v1.2.3 - 2023-01-01' in entry_no_commits
        assert 'Version bump release.' in entry_no_commits

    def test_all_commands_implemented():
        cli = CLIInterface()
        
        # Test that all commands are now fully implemented (no more placeholders)
        # This test verifies that all major commands execute without "implementation pending" messages
        
        # Test release_info_command is implemented
        mock_release_info = ReleaseInfo(
            version="v1.2.3",
            timestamp="2023-01-01T10:00:00",
            commit_hash="abc1234",
            commits=[],
            previous_version="v1.2.2"
        )
        
        with mock.patch.object(cli, 'generate_release_info', return_value=mock_release_info):
            with mock.patch('builtins.open', mock.mock_open()) as mock_file:
                with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                    result = cli._execute_release_info_command()
                    assert result == 0
                    output = mock_stdout.getvalue()
                    assert 'implementation pending' not in output
                    assert 'Generating release information' in output
                    assert 'Generated version.json' in output
        
        # All other commands (release_diff, release_last, release_prepare) are also fully implemented
        # and tested in their respective test functions
    
    # Run all tests
    print("\nRunning CLIInterface unit tests...")
    print("=" * 50)
    
    tests = [
        ("parse_arguments", test_parse_arguments),
        ("argument_validation", test_argument_validation),
        ("execute_view_command", test_execute_view_command),
        ("execute_increment_command", test_execute_increment_command),
        ("rollback_mechanism", test_rollback_mechanism),
        ("increment_integration", test_increment_integration),
        ("execute_command_routing", test_execute_command_routing),
        ("execute_release_prepare_command", test_execute_release_prepare_command),
        ("update_version_json", test_update_version_json),
        ("update_changelog", test_update_changelog),
        ("update_releases", test_update_releases),
        ("generate_changelog_entry", test_generate_changelog_entry),
        ("generate_releases_entry", test_generate_releases_entry),
        ("all_commands_implemented", test_all_commands_implemented),
        ("generate_release_info", test_generate_release_info),
        ("generate_release_info_no_git", test_generate_release_info_no_git),
        ("generate_release_info_git_errors", test_generate_release_info_git_errors),
        ("format_release_notes", test_format_release_notes),
    ]
    
    passed = 0
    for test_name, test_func in tests:
        if run_test(test_name, test_func):
            passed += 1
    
    # Print results
    for result in test_results:
        print(result)
    
    print("=" * 50)
    print(f"Tests passed: {passed}/{len(tests)}")
    
    if passed == len(tests):
        print("All CLIInterface tests passed! ✓")
        return True
    else:
        print("Some tests failed! ✗")
        return False


# Unit Tests for VersionManager
def test_version_manager():
    """Comprehensive unit tests for VersionManager class"""
    import sys
    
    vm = VersionManager()
    test_results = []
    
    def run_test(test_name: str, test_func):
        """Helper to run individual tests and track results"""
        try:
            test_func()
            test_results.append(f"✓ {test_name}")
            return True
        except Exception as e:
            test_results.append(f"✗ {test_name}: {e}")
            return False
    
    # Test parse_version method
    def test_parse_version():
        # Valid versions with v prefix
        assert vm.parse_version("v1.2.3") == (1, 2, 3)
        assert vm.parse_version("v0.0.1") == (0, 0, 1)
        assert vm.parse_version("v10.20.30") == (10, 20, 30)
        
        # Valid versions without v prefix
        assert vm.parse_version("1.2.3") == (1, 2, 3)
        assert vm.parse_version("0.0.1") == (0, 0, 1)
        
        # Test with whitespace
        assert vm.parse_version(" v1.2.3 ") == (1, 2, 3)
        
        # Invalid versions should raise VersionError
        try:
            vm.parse_version("")
            assert False, "Should raise VersionError for empty string"
        except VersionError:
            pass
        
        try:
            vm.parse_version("1.2")
            assert False, "Should raise VersionError for incomplete version"
        except VersionError:
            pass
        
        try:
            vm.parse_version("v1.2.3.4")
            assert False, "Should raise VersionError for too many parts"
        except VersionError:
            pass
        
        try:
            vm.parse_version("invalid")
            assert False, "Should raise VersionError for invalid format"
        except VersionError:
            pass
    
    # Test compare_versions method
    def test_compare_versions():
        # Equal versions
        assert vm.compare_versions("v1.2.3", "v1.2.3") == 0
        assert vm.compare_versions("1.2.3", "v1.2.3") == 0
        
        # First version less than second
        assert vm.compare_versions("v1.2.3", "v1.2.4") == -1
        assert vm.compare_versions("v1.2.3", "v1.3.0") == -1
        assert vm.compare_versions("v1.2.3", "v2.0.0") == -1
        assert vm.compare_versions("v0.9.9", "v1.0.0") == -1
        
        # First version greater than second
        assert vm.compare_versions("v1.2.4", "v1.2.3") == 1
        assert vm.compare_versions("v1.3.0", "v1.2.3") == 1
        assert vm.compare_versions("v2.0.0", "v1.2.3") == 1
        assert vm.compare_versions("v1.0.0", "v0.9.9") == 1
        
        # Test with invalid versions
        try:
            vm.compare_versions("invalid", "v1.2.3")
            assert False, "Should raise VersionError for invalid version"
        except VersionError:
            pass
    
    # Test find_highest_version method
    def test_find_highest_version():
        # Normal case with multiple versions
        versions = ["v1.2.3", "v1.2.4", "v1.1.0", "v2.0.0"]
        assert vm.find_highest_version(versions) == "v2.0.0"
        
        # Mixed prefix styles
        versions = ["1.2.3", "v1.2.4", "v1.1.0", "2.0.0"]
        assert vm.find_highest_version(versions) == "2.0.0"
        
        # Single version
        assert vm.find_highest_version(["v1.2.3"]) == "v1.2.3"
        
        # Versions with some invalid entries (should skip invalid)
        versions = ["v1.2.3", "invalid", "v1.2.4", "v1.1.0"]
        assert vm.find_highest_version(versions) == "v1.2.4"
        
        # Empty list should raise error
        try:
            vm.find_highest_version([])
            assert False, "Should raise VersionError for empty list"
        except VersionError:
            pass
        
        # All invalid versions should raise error
        try:
            vm.find_highest_version(["invalid1", "invalid2"])
            assert False, "Should raise VersionError for all invalid versions"
        except VersionError:
            pass
    
    # Test increment_patch method
    def test_increment_patch():
        assert vm.increment_patch("v1.2.3") == "v1.2.4"
        assert vm.increment_patch("1.2.3") == "1.2.4"
        assert vm.increment_patch("v0.0.0") == "v0.0.1"
        assert vm.increment_patch("v1.2.9") == "v1.2.10"
        
        # Invalid version should raise error
        try:
            vm.increment_patch("invalid")
            assert False, "Should raise VersionError for invalid version"
        except VersionError:
            pass
    
    # Test increment_minor method
    def test_increment_minor():
        assert vm.increment_minor("v1.2.3") == "v1.3.0"
        assert vm.increment_minor("1.2.3") == "1.3.0"
        assert vm.increment_minor("v0.0.9") == "v0.1.0"
        assert vm.increment_minor("v1.9.5") == "v1.10.0"
        
        # Invalid version should raise error
        try:
            vm.increment_minor("invalid")
            assert False, "Should raise VersionError for invalid version"
        except VersionError:
            pass
    
    # Test increment_major method
    def test_increment_major():
        assert vm.increment_major("v1.2.3") == "v2.0.0"
        assert vm.increment_major("1.2.3") == "2.0.0"
        assert vm.increment_major("v0.9.9") == "v1.0.0"
        assert vm.increment_major("v9.5.2") == "v10.0.0"
        
        # Invalid version should raise error
        try:
            vm.increment_major("invalid")
            assert False, "Should raise VersionError for invalid version"
        except VersionError:
            pass
    
    # Run all tests
    print("\nRunning VersionManager unit tests...")
    print("=" * 50)
    
    tests = [
        ("parse_version", test_parse_version),
        ("compare_versions", test_compare_versions),
        ("find_highest_version", test_find_highest_version),
        ("increment_patch", test_increment_patch),
        ("increment_minor", test_increment_minor),
        ("increment_major", test_increment_major),
    ]
    
    passed = 0
    for test_name, test_func in tests:
        if run_test(test_name, test_func):
            passed += 1
    
    # Print results
    for result in test_results:
        print(result)
    
    print("=" * 50)
    print(f"Tests passed: {passed}/{len(tests)}")
    
    if passed == len(tests):
        print("All VersionManager tests passed! ✓")
        return True
    else:
        print("Some tests failed! ✗")
        return False


def test_file_manager():
    """Comprehensive unit tests for FileManager class"""
    import tempfile
    import shutil
    
    test_results = []
    
    def run_test(test_name: str, test_func):
        """Helper to run individual tests and track results"""
        try:
            test_func()
            test_results.append(f"✓ {test_name}")
            return True
        except Exception as e:
            test_results.append(f"✗ {test_name}: {e}")
            return False
    
    # Test FileManager initialization and validation
    def test_file_manager_init():
        # Valid configuration
        valid_config = [
            {
                'file': 'test.py',
                'pattern': re.compile(r'version = "(v\d+\.\d+\.\d+)"'),
                'template': 'version = "{version}"',
            }
        ]
        fm = FileManager(valid_config)
        assert len(fm.file_configs) == 1
        
        # Empty configuration should raise error
        try:
            FileManager([])
            assert False, "Should raise FileError for empty config"
        except FileError:
            pass
        
        # Missing required keys
        try:
            FileManager([{'file': 'test.py'}])
            assert False, "Should raise FileError for missing keys"
        except FileError:
            pass
        
        # Invalid pattern type
        try:
            FileManager([{
                'file': 'test.py',
                'pattern': 'not a regex',
                'template': 'version = "{version}"'
            }])
            assert False, "Should raise FileError for invalid pattern"
        except FileError:
            pass
        
        # Template without {version} placeholder
        try:
            FileManager([{
                'file': 'test.py',
                'pattern': re.compile(r'version = "(v\d+\.\d+\.\d+)"'),
                'template': 'version = "1.0.0"'
            }])
            assert False, "Should raise FileError for template without placeholder"
        except FileError:
            pass
        
        # Pattern without capture group
        try:
            FileManager([{
                'file': 'test.py',
                'pattern': re.compile(r'version = "v\d+\.\d+\.\d+"'),
                'template': 'version = "{version}"'
            }])
            assert False, "Should raise FileError for pattern without capture group"
        except FileError:
            pass
    
    # Test file pattern matching
    def test_file_pattern_matching():
        config = [
            {
                'file': 'test.py',
                'pattern': re.compile(r'version = "(v\d+\.\d+\.\d+)"'),
                'template': 'version = "{version}"',
            },
            {
                'file': '*.py',
                'pattern': re.compile(r'VERSION = "(v\d+\.\d+\.\d+)"'),
                'template': 'VERSION = "{version}"',
            }
        ]
        fm = FileManager(config)
        
        # Test direct file matching
        assert fm._file_matches_pattern('test.py', 'test.py')
        assert not fm._file_matches_pattern('other.py', 'test.py')
        
        # Test glob pattern matching
        assert fm._file_matches_pattern('app.py', '*.py')
        assert fm._file_matches_pattern('main.py', '*.py')
        assert not fm._file_matches_pattern('readme.txt', '*.py')
    
    # Test expand_file_patterns with temporary files
    def test_expand_file_patterns():
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            test_files = ['app.py', 'main.py', 'config.json', 'subdir/module.py']
            for file_path in test_files:
                full_path = os.path.join(temp_dir, file_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'w') as f:
                    f.write('# test file')
            
            # Change to temp directory for glob operations
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                config = [
                    {
                        'file': 'app.py',
                        'pattern': re.compile(r'version = "(v\d+\.\d+\.\d+)"'),
                        'template': 'version = "{version}"',
                    },
                    {
                        'file': '*.py',
                        'pattern': re.compile(r'VERSION = "(v\d+\.\d+\.\d+)"'),
                        'template': 'VERSION = "{version}"',
                    },
                    {
                        'file': 'nonexistent.py',
                        'pattern': re.compile(r'version = "(v\d+\.\d+\.\d+)"'),
                        'template': 'version = "{version}"',
                    }
                ]
                fm = FileManager(config)
                
                expanded = fm.expand_file_patterns()
                
                # Should find app.py, main.py (from *.py pattern)
                # app.py might appear twice but should be deduplicated
                assert 'app.py' in expanded
                assert 'main.py' in expanded
                assert 'config.json' not in expanded  # Not matching any pattern
                
            finally:
                os.chdir(original_cwd)
    
    # Test find_versions_in_files
    def test_find_versions_in_files():
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files with versions
            test_file1 = os.path.join(temp_dir, 'app.py')
            with open(test_file1, 'w') as f:
                f.write('#!/usr/bin/env python3\nversion = "v1.2.3"\nprint("Hello")')
            
            test_file2 = os.path.join(temp_dir, 'config.py')
            with open(test_file2, 'w') as f:
                f.write('CONFIG_VERSION = "v2.1.0"\nother_setting = "value"')
            
            test_file3 = os.path.join(temp_dir, 'no_version.py')
            with open(test_file3, 'w') as f:
                f.write('print("No version here")')
            
            # Change to temp directory
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                config = [
                    {
                        'file': 'app.py',
                        'pattern': re.compile(r'version = "(v\d+\.\d+\.\d+)"'),
                        'template': 'version = "{version}"',
                    },
                    {
                        'file': 'config.py',
                        'pattern': re.compile(r'CONFIG_VERSION = "(v\d+\.\d+\.\d+)"'),
                        'template': 'CONFIG_VERSION = "{version}"',
                    },
                    {
                        'file': 'no_version.py',
                        'pattern': re.compile(r'version = "(v\d+\.\d+\.\d+)"'),
                        'template': 'version = "{version}"',
                    }
                ]
                fm = FileManager(config)
                
                versions = fm.find_versions_in_files()
                
                assert versions['app.py'] == 'v1.2.3'
                assert versions['config.py'] == 'v2.1.0'
                assert 'no_version.py' not in versions  # No version found
                
            finally:
                os.chdir(original_cwd)
    
    # Test update_file_version
    def test_update_file_version():
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test file with version
            test_file = os.path.join(temp_dir, 'app.py')
            original_content = '#!/usr/bin/env python3\nversion = "v1.2.3"\nprint("Hello")'
            with open(test_file, 'w') as f:
                f.write(original_content)
            
            # Change to temp directory
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                config = [
                    {
                        'file': 'app.py',
                        'pattern': re.compile(r'version = "(v\d+\.\d+\.\d+)"'),
                        'template': 'version = "{version}"',
                    }
                ]
                fm = FileManager(config)
                
                # Update version
                success = fm.update_file_version('app.py', 'v2.0.0')
                assert success
                
                # Verify file was updated
                with open(test_file, 'r') as f:
                    updated_content = f.read()
                
                assert 'version = "v2.0.0"' in updated_content
                assert 'version = "v1.2.3"' not in updated_content
                assert '#!/usr/bin/env python3' in updated_content  # Other content preserved
                
                # Test updating file with no version (should return False)
                # First add configuration for the no_version file
                config.append({
                    'file': 'no_version.py',
                    'pattern': re.compile(r'version = "(v\d+\.\d+\.\d+)"'),
                    'template': 'version = "{version}"',
                })
                fm = FileManager(config)  # Recreate with updated config
                
                test_file2 = os.path.join(temp_dir, 'no_version.py')
                with open(test_file2, 'w') as f:
                    f.write('print("No version")')
                
                success = fm.update_file_version('no_version.py', 'v1.0.0')
                assert not success  # Should return False when no version found
                
            finally:
                os.chdir(original_cwd)
    
    # Test update_all_files
    def test_update_all_files():
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create multiple test files
            files_content = {
                'app.py': 'version = "v1.0.0"\nprint("App")',
                'config.py': 'VERSION = "v1.0.0"\nconfig = {}',
                'no_version.py': 'print("No version")'
            }
            
            for filename, content in files_content.items():
                with open(os.path.join(temp_dir, filename), 'w') as f:
                    f.write(content)
            
            # Change to temp directory
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                config = [
                    {
                        'file': 'app.py',
                        'pattern': re.compile(r'version = "(v\d+\.\d+\.\d+)"'),
                        'template': 'version = "{version}"',
                    },
                    {
                        'file': 'config.py',
                        'pattern': re.compile(r'VERSION = "(v\d+\.\d+\.\d+)"'),
                        'template': 'VERSION = "{version}"',
                    },
                    {
                        'file': 'no_version.py',
                        'pattern': re.compile(r'version = "(v\d+\.\d+\.\d+)"'),
                        'template': 'version = "{version}"',
                    }
                ]
                fm = FileManager(config)
                
                # Update all files
                results = fm.update_all_files('v2.5.0')
                
                # Check results
                assert results['app.py'] == True
                assert results['config.py'] == True
                assert results['no_version.py'] == False  # No version to update
                
                # Verify files were updated
                with open('app.py', 'r') as f:
                    assert 'version = "v2.5.0"' in f.read()
                
                with open('config.py', 'r') as f:
                    assert 'VERSION = "v2.5.0"' in f.read()
                
            finally:
                os.chdir(original_cwd)
    
    # Run all tests
    print("\nRunning FileManager unit tests...")
    print("=" * 50)
    
    tests = [
        ("file_manager_init", test_file_manager_init),
        ("file_pattern_matching", test_file_pattern_matching),
        ("expand_file_patterns", test_expand_file_patterns),
        ("find_versions_in_files", test_find_versions_in_files),
        ("update_file_version", test_update_file_version),
        ("update_all_files", test_update_all_files),
    ]
    
    passed = 0
    for test_name, test_func in tests:
        if run_test(test_name, test_func):
            passed += 1
    
    # Print results
    for result in test_results:
        print(result)
    
    print("=" * 50)
    print(f"Tests passed: {passed}/{len(tests)}")
    
    if passed == len(tests):
        print("All FileManager tests passed! ✓")
        return True
    else:
        print("Some tests failed! ✗")
        return False


def test_git_manager():
    """Comprehensive unit tests for GitManager class with mocked git operations"""
    import unittest.mock as mock
    
    test_results = []
    
    def run_test(test_name: str, test_func):
        """Helper to run individual tests and track results"""
        try:
            test_func()
            test_results.append(f"✓ {test_name}")
            return True
        except Exception as e:
            test_results.append(f"✗ {test_name}: {e}")
            return False
    
    # Test is_git_repository method
    def test_is_git_repository():
        gm = GitManager()
        
        # Mock successful git command
        with mock.patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            assert gm.is_git_repository() == True
            mock_run.assert_called_with(
                ['git', 'rev-parse', '--git-dir'],
                capture_output=True,
                text=True,
                timeout=10
            )
        
        # Mock failed git command (not a git repo)
        with mock.patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 1
            assert gm.is_git_repository() == False
        
        # Mock git command not found
        with mock.patch('subprocess.run', side_effect=FileNotFoundError):
            assert gm.is_git_repository() == False
        
        # Mock timeout
        with mock.patch('subprocess.run', side_effect=subprocess.TimeoutExpired('git', 10)):
            assert gm.is_git_repository() == False
    
    # Test get_git_tags method
    def test_get_git_tags():
        gm = GitManager()
        
        # Mock not in git repository
        with mock.patch.object(gm, 'is_git_repository', return_value=False):
            try:
                gm.get_git_tags()
                assert False, "Should raise GitError for non-git repository"
            except GitError as e:
                assert "Not in a git repository" in str(e)
        
        # Mock successful git tags command with version tags
        with mock.patch.object(gm, 'is_git_repository', return_value=True):
            with mock.patch('subprocess.run') as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = "v1.0.0\nv1.2.0\nv1.1.0\nv2.0.0\nnon-version-tag\n"
                
                tags = gm.get_git_tags()
                
                # Should return version tags sorted by version (highest first)
                expected_tags = ["v2.0.0", "v1.2.0", "v1.1.0", "v1.0.0"]
                assert tags == expected_tags
        
        # Mock empty tags
        with mock.patch.object(gm, 'is_git_repository', return_value=True):
            with mock.patch('subprocess.run') as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = ""
                
                tags = gm.get_git_tags()
                assert tags == []
        
        # Mock git command failure
        with mock.patch.object(gm, 'is_git_repository', return_value=True):
            with mock.patch('subprocess.run') as mock_run:
                mock_run.return_value.returncode = 1
                mock_run.return_value.stderr = "fatal: not a git repository"
                
                try:
                    gm.get_git_tags()
                    assert False, "Should raise GitError for failed git command"
                except GitError as e:
                    assert "Git tag command failed" in str(e)
        
        # Mock timeout
        with mock.patch.object(gm, 'is_git_repository', return_value=True):
            with mock.patch('subprocess.run', side_effect=subprocess.TimeoutExpired('git', 30)):
                try:
                    gm.get_git_tags()
                    assert False, "Should raise GitError for timeout"
                except GitError as e:
                    assert "timed out" in str(e)
    
    # Test get_commits_between_tags method
    def test_get_commits_between_tags():
        gm = GitManager()
        
        # Mock not in git repository
        with mock.patch.object(gm, 'is_git_repository', return_value=False):
            try:
                gm.get_commits_between_tags("v1.0.0", "v1.1.0")
                assert False, "Should raise GitError for non-git repository"
            except GitError as e:
                assert "Not in a git repository" in str(e)
        
        # Mock successful commits between tags
        with mock.patch.object(gm, 'is_git_repository', return_value=True):
            with mock.patch('subprocess.run') as mock_run:
                # Mock tag verification (both calls succeed)
                mock_run.side_effect = [
                    mock.Mock(returncode=0),  # First tag verification
                    mock.Mock(returncode=0),  # Second tag verification
                    mock.Mock(  # Git log command
                        returncode=0,
                        stdout="abc123|Fix bug in parser|John Doe|2023-01-15 10:30:00 +0000\ndef456|Add new feature|Jane Smith|2023-01-16 14:20:00 +0000"
                    )
                ]
                
                commits = gm.get_commits_between_tags("v1.0.0", "v1.1.0")
                
                expected_commits = [
                    {
                        'hash': 'abc123',
                        'message': 'Fix bug in parser',
                        'author': 'John Doe',
                        'date': '2023-01-15 10:30:00 +0000'
                    },
                    {
                        'hash': 'def456',
                        'message': 'Add new feature',
                        'author': 'Jane Smith',
                        'date': '2023-01-16 14:20:00 +0000'
                    }
                ]
                assert commits == expected_commits
        
        # Mock invalid tag
        with mock.patch.object(gm, 'is_git_repository', return_value=True):
            with mock.patch('subprocess.run') as mock_run:
                mock_run.return_value.returncode = 1  # Tag verification fails
                
                try:
                    gm.get_commits_between_tags("invalid-tag", "v1.1.0")
                    assert False, "Should raise GitError for invalid tag"
                except GitError as e:
                    assert "does not exist" in str(e)
        
        # Mock git log command failure
        with mock.patch.object(gm, 'is_git_repository', return_value=True):
            with mock.patch('subprocess.run') as mock_run:
                mock_run.side_effect = [
                    mock.Mock(returncode=0),  # First tag verification
                    mock.Mock(returncode=0),  # Second tag verification
                    mock.Mock(returncode=1, stderr="fatal: bad revision")  # Git log fails
                ]
                
                try:
                    gm.get_commits_between_tags("v1.0.0", "v1.1.0")
                    assert False, "Should raise GitError for failed git log"
                except GitError as e:
                    assert "Git log command failed" in str(e)
    
    # Test get_commits_since_tag method
    def test_get_commits_since_tag():
        gm = GitManager()
        
        # Mock not in git repository
        with mock.patch.object(gm, 'is_git_repository', return_value=False):
            try:
                gm.get_commits_since_tag("v1.0.0")
                assert False, "Should raise GitError for non-git repository"
            except GitError as e:
                assert "Not in a git repository" in str(e)
        
        # Mock successful commits since tag
        with mock.patch.object(gm, 'is_git_repository', return_value=True):
            with mock.patch('subprocess.run') as mock_run:
                mock_run.side_effect = [
                    mock.Mock(returncode=0),  # Tag verification
                    mock.Mock(  # Git log command
                        returncode=0,
                        stdout="xyz789|Latest commit|Alice Brown|2023-01-17 09:15:00 +0000"
                    )
                ]
                
                commits = gm.get_commits_since_tag("v1.0.0")
                
                expected_commits = [
                    {
                        'hash': 'xyz789',
                        'message': 'Latest commit',
                        'author': 'Alice Brown',
                        'date': '2023-01-17 09:15:00 +0000'
                    }
                ]
                assert commits == expected_commits
        
        # Mock invalid tag
        with mock.patch.object(gm, 'is_git_repository', return_value=True):
            with mock.patch('subprocess.run') as mock_run:
                mock_run.return_value.returncode = 1  # Tag verification fails
                
                try:
                    gm.get_commits_since_tag("invalid-tag")
                    assert False, "Should raise GitError for invalid tag"
                except GitError as e:
                    assert "does not exist" in str(e)
    
    # Test get_latest_tag method
    def test_get_latest_tag():
        gm = GitManager()
        
        # Mock successful case with tags
        with mock.patch.object(gm, 'get_git_tags', return_value=["v2.0.0", "v1.2.0", "v1.1.0"]):
            latest = gm.get_latest_tag()
            assert latest == "v2.0.0"
        
        # Mock no tags case
        with mock.patch.object(gm, 'get_git_tags', return_value=[]):
            try:
                gm.get_latest_tag()
                assert False, "Should raise GitError when no tags exist"
            except GitError as e:
                assert "No git tags found" in str(e)
    
    # Test get_current_commit_hash method
    def test_get_current_commit_hash():
        gm = GitManager()
        
        # Mock not in git repository
        with mock.patch.object(gm, 'is_git_repository', return_value=False):
            try:
                gm.get_current_commit_hash()
                assert False, "Should raise GitError for non-git repository"
            except GitError as e:
                assert "Not in a git repository" in str(e)
        
        # Mock successful commit hash retrieval
        with mock.patch.object(gm, 'is_git_repository', return_value=True):
            with mock.patch('subprocess.run') as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = "abc1234\n"
                
                commit_hash = gm.get_current_commit_hash()
                assert commit_hash == "abc1234"
        
        # Mock git command failure
        with mock.patch.object(gm, 'is_git_repository', return_value=True):
            with mock.patch('subprocess.run') as mock_run:
                mock_run.return_value.returncode = 1
                mock_run.return_value.stderr = "fatal: bad revision 'HEAD'"
                
                try:
                    gm.get_current_commit_hash()
                    assert False, "Should raise GitError for failed git command"
                except GitError as e:
                    assert "Git rev-parse command failed" in str(e)
    
    # Test get_all_commits_since_beginning method
    def test_get_all_commits_since_beginning():
        gm = GitManager()
        
        # Mock not in git repository
        with mock.patch.object(gm, 'is_git_repository', return_value=False):
            try:
                gm.get_all_commits_since_beginning()
                assert False, "Should raise GitError for non-git repository"
            except GitError as e:
                assert "Not in a git repository" in str(e)
        
        # Mock successful all commits retrieval
        with mock.patch.object(gm, 'is_git_repository', return_value=True):
            with mock.patch('subprocess.run') as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = "abc123|Initial commit|John Doe|2023-01-01 10:00:00 +0000\ndef456|Second commit|Jane Smith|2023-01-02 11:00:00 +0000"
                
                commits = gm.get_all_commits_since_beginning()
                
                expected_commits = [
                    {
                        'hash': 'abc123',
                        'message': 'Initial commit',
                        'author': 'John Doe',
                        'date': '2023-01-01 10:00:00 +0000'
                    },
                    {
                        'hash': 'def456',
                        'message': 'Second commit',
                        'author': 'Jane Smith',
                        'date': '2023-01-02 11:00:00 +0000'
                    }
                ]
                assert commits == expected_commits
        
        # Mock git command failure
        with mock.patch.object(gm, 'is_git_repository', return_value=True):
            with mock.patch('subprocess.run') as mock_run:
                mock_run.return_value.returncode = 1
                mock_run.return_value.stderr = "fatal: your current branch does not have any commits yet"
                
                try:
                    gm.get_all_commits_since_beginning()
                    assert False, "Should raise GitError for failed git command"
                except GitError as e:
                    assert "Git log command failed" in str(e)
    
    # Run all tests
    print("\nRunning GitManager unit tests...")
    print("=" * 50)
    
    tests = [
        ("is_git_repository", test_is_git_repository),
        ("get_git_tags", test_get_git_tags),
        ("get_commits_between_tags", test_get_commits_between_tags),
        ("get_commits_since_tag", test_get_commits_since_tag),
        ("get_latest_tag", test_get_latest_tag),
        ("get_current_commit_hash", test_get_current_commit_hash),
        ("get_all_commits_since_beginning", test_get_all_commits_since_beginning),
    ]
    
    passed = 0
    for test_name, test_func in tests:
        if run_test(test_name, test_func):
            passed += 1
    
    # Print results
    for result in test_results:
        print(result)
    
    print("=" * 50)
    print(f"Tests passed: {passed}/{len(tests)}")
    
    if passed == len(tests):
        print("All GitManager tests passed! ✓")
        return True
    else:
        print("Some tests failed! ✗")
        return False


if __name__ == "__main__":
    # Check if running tests
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("Running all unit tests for v-and-r...")
        print("=" * 60)
        
        main_success = test_main_execution_flow()
        cli_success = test_cli_interface()
        version_success = test_version_manager()
        file_success = test_file_manager()
        git_success = test_git_manager()
        
        overall_success = main_success and cli_success and version_success and file_success and git_success
        
        print("\n" + "=" * 60)
        if overall_success:
            print("All tests passed! ✓")
        else:
            print("Some tests failed! ✗")
        
        sys.exit(0 if overall_success else 1)
    else:
        main()