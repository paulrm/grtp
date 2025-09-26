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


if __name__ == "__main__":
    # Check if running tests
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        success = test_version_manager()
        sys.exit(0 if success else 1)
    else:
        main()