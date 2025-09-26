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


# VERSION_FILES Configuration
VERSION_FILES = [
    {
        'file': 'app.py',
        'pattern': re.compile(r'version = "(v\d+\.\d+\.\d+)"'),
        'template': 'version = "{version}"',
    },
    {
        'file': 'README.md', 
        'pattern': re.compile(r'- Version (v\d+\.\d+\.\d+)'),
        'template': '- Version {version}',
    },
    {
        'file': 'dags/*.py',
        'pattern': re.compile(r'Version: (v\d+\.\d+\.\d+)'),
        'template': 'Version: {version}',
    }
]


def main():
    """Main entry point for the v-and-r tool"""
    print("v-and-r (Version and Release Manager)")
    print("Basic structure initialized - implementation in progress...")


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


if __name__ == "__main__":
    # Check if running tests
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("Running all unit tests for v-and-r...")
        print("=" * 60)
        
        version_success = test_version_manager()
        file_success = test_file_manager()
        
        overall_success = version_success and file_success
        
        print("\n" + "=" * 60)
        if overall_success:
            print("All tests passed! ✓")
        else:
            print("Some tests failed! ✗")
        
        sys.exit(0 if overall_success else 1)
    else:
        main()