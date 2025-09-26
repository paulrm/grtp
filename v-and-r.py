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
VERSION_FILES = [
    {
        'file': 'README.md', 
        'pattern': re.compile(r'- Version (v\d+\.\d+\.\d+)'),
        'template': '- Version {version}',
    },    
    {
        'file': 'sample/*.py',
        'pattern': re.compile(r'version = "(v\d+\.\d+\.\d+)"'),
        'template': 'version = "{version}"',
    },
    {
        'file': 'sample/*.py',
        'pattern': re.compile(r'Version: (v\d+\.\d+\.\d+)'),
        'template': 'Version: {version}',
    }
]


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
        try:
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
                
        except (VAndRError, VersionError, FileError, GitError) as e:
            print(f"Error: {e}")
            return 1
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            return 130
        except Exception as e:
            print(f"Unexpected error: {e}")
            return 1
    
    def _execute_view_command(self) -> int:
        """
        Execute view command to display current versions.
        
        Returns:
            Exit code (0 for success, 1 for failure)
        """
        print("v-and-r (Version and Release Manager)")
        print("=" * 50)
        print("Current versions across configured files:")
        print()
        
        try:
            versions_found = self.file_manager.find_versions_in_files()
            
            if not versions_found:
                print("No versions found in any configured files.")
                print("\nConfigured file patterns:")
                for config in self.file_manager.file_configs:
                    print(f"  - {config.file_pattern}")
                return 0
            
            # Display found versions
            for file_path, version in versions_found.items():
                print(f"  {file_path}: {version}")
            
            # Highlight highest version if multiple versions exist
            if len(versions_found) > 1:
                try:
                    highest_version = self.version_manager.find_highest_version(list(versions_found.values()))
                    print(f"\nHighest version: {highest_version}")
                except VersionError as e:
                    print(f"\nWarning: Could not determine highest version: {e}")
            
            return 0
            
        except FileError as e:
            print(f"File error: {e}")
            return 1
    
    def _execute_increment_command(self, increment_type: str) -> int:
        """
        Execute version increment command.
        
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
                return 1
            
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
            
            print(f"New version: {new_version}")
            print()
            
            # Update all files
            print("Updating files...")
            update_results = self.file_manager.update_all_files(new_version)
            
            success_count = 0
            for file_path, success in update_results.items():
                status = "✓" if success else "✗"
                print(f"  {status} {file_path}")
                if success:
                    success_count += 1
            
            print()
            if success_count == len(update_results):
                print(f"Successfully updated {success_count} files to version {new_version}")
                return 0
            else:
                print(f"Updated {success_count}/{len(update_results)} files. Some updates failed.")
                return 1
                
        except (VersionError, FileError) as e:
            print(f"Error: {e}")
            return 1
    
    def _execute_release_info_command(self) -> int:
        """
        Execute release info command to generate version.json.
        
        Returns:
            Exit code (0 for success, 1 for failure)
        """
        print("v-and-r: Generating release information")
        print("=" * 50)
        
        # This is a placeholder - full implementation will be in task 8
        print("Release info generation - implementation pending")
        return 0
    
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
        
        # This is a placeholder - full implementation will be in task 9
        print("Release diff - implementation pending")
        return 0
    
    def _execute_release_last_command(self) -> int:
        """
        Execute release last command to show commits since last tag.
        
        Returns:
            Exit code (0 for success, 1 for failure)
        """
        print("v-and-r: Commits since last release")
        print("=" * 50)
        
        # This is a placeholder - full implementation will be in task 9
        print("Release last - implementation pending")
        return 0
    
    def _execute_release_prepare_command(self) -> int:
        """
        Execute release prepare command to update documentation.
        
        Returns:
            Exit code (0 for success, 1 for failure)
        """
        print("v-and-r: Preparing release documentation")
        print("=" * 50)
        
        # This is a placeholder - full implementation will be in task 10
        print("Release prepare - implementation pending")
        return 0


def main():
    """Main entry point for the v-and-r tool"""
    cli = CLIInterface()
    args = cli.parse_arguments()
    exit_code = cli.execute_command(args)
    sys.exit(exit_code)


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
        
        # Mock successful increment
        mock_versions = {'app.py': 'v1.2.3'}
        mock_update_results = {'app.py': True}
        
        with mock.patch.object(cli.file_manager, 'find_versions_in_files', return_value=mock_versions):
            with mock.patch.object(cli.file_manager, 'update_all_files', return_value=mock_update_results):
                with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                    result = cli._execute_increment_command('patch')
                    assert result == 0
                    output = mock_stdout.getvalue()
                    assert 'v1.2.3' in output
                    assert 'v1.2.4' in output
                    assert '✓ app.py' in output
        
        # Test no versions found
        with mock.patch.object(cli.file_manager, 'find_versions_in_files', return_value={}):
            with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                result = cli._execute_increment_command('patch')
                assert result == 1
                output = mock_stdout.getvalue()
                assert 'No versions found' in output
        
        # Test partial update failure
        mock_update_results_partial = {'app.py': True, 'README.md': False}
        with mock.patch.object(cli.file_manager, 'find_versions_in_files', return_value=mock_versions):
            with mock.patch.object(cli.file_manager, 'update_all_files', return_value=mock_update_results_partial):
                with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                    result = cli._execute_increment_command('minor')
                    assert result == 1
                    output = mock_stdout.getvalue()
                    assert 'v1.3.0' in output
                    assert 'Some updates failed' in output
    
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
    
    def test_placeholder_commands():
        cli = CLIInterface()
        
        # Test placeholder commands return 0 and print appropriate messages
        with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = cli._execute_release_info_command()
            assert result == 0
            output = mock_stdout.getvalue()
            assert 'implementation pending' in output
        
        with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = cli._execute_release_diff_command('v1.0.0', 'v1.1.0')
            assert result == 0
            output = mock_stdout.getvalue()
            assert 'implementation pending' in output
        
        with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = cli._execute_release_last_command()
            assert result == 0
            output = mock_stdout.getvalue()
            assert 'implementation pending' in output
        
        with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = cli._execute_release_prepare_command()
            assert result == 0
            output = mock_stdout.getvalue()
            assert 'implementation pending' in output
    
    # Run all tests
    print("\nRunning CLIInterface unit tests...")
    print("=" * 50)
    
    tests = [
        ("parse_arguments", test_parse_arguments),
        ("argument_validation", test_argument_validation),
        ("execute_view_command", test_execute_view_command),
        ("execute_increment_command", test_execute_increment_command),
        ("execute_command_routing", test_execute_command_routing),
        ("placeholder_commands", test_placeholder_commands),
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
        
        cli_success = test_cli_interface()
        version_success = test_version_manager()
        file_success = test_file_manager()
        git_success = test_git_manager()
        
        overall_success = cli_success and version_success and file_success and git_success
        
        print("\n" + "=" * 60)
        if overall_success:
            print("All tests passed! ✓")
        else:
            print("Some tests failed! ✗")
        
        sys.exit(0 if overall_success else 1)
    else:
        main()