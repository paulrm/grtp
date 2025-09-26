# Product Overview

## v-and-r - Version and Release Manager

A command-line tool that automates version management and release processes across multiple project files. The tool follows semantic versioning principles and integrates with git for release management.
Prototype in Python, but limited.


### Core Features
- **Version Discovery**: Scans configured files to find and display current versions
- **Semantic Versioning**: Supports patch, minor, and major version increments
- **Multi-file Updates**: Updates version numbers across multiple files using configurable patterns
- **Release Management**: Generates release notes and compares commits between versions
- **Git Integration**: Leverages git tags and commit history for release tracking

### Target Users
Developers and teams who need to maintain consistent version numbers across multiple files in their projects and want automated release management capabilities.

### Key Value Proposition
Eliminates manual version management errors and provides a single command interface for version control and release documentation.

### Use of CHANGELOG.md and RELEASES.md

| Aspect               | `CHANGELOG.md`                                                              | `RELEASES.md` / GitHub Releases                                                  |
| -------------------- | --------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| Primary purpose      | Human-readable history of changes across versions in the repo               | Announce and package each release (notes + assets) for end users                 |
| Audience             | Contributors, maintainers, power users                                      | Users/installers, downstream integrators, package managers                       |
| Location             | Tracked file in the repo root                                               | Git tag page on hosting (e.g., GitHub), optionally mirrored in `RELEASES.md`     |
| Source of truth      | Commit-driven, lives with code; easy to diff in PRs                         | Tag-driven; each release corresponds to a tag (e.g., `v1.4.0`)                   |
| Granularity          | Complete history; can include Unreleased section                            | Per-release highlights; focuses on what’s new in that release                    |
| Typical structure    | Headings by version/date, categorized entries (Added/Changed/Fixed/Removed) | Title = version, body = highlights/breaking changes/migration, assets (binaries) |
| Standards            | Often follows **Keep a Changelog** + **SemVer**                             | Often mirrors highlights from changelog; supports markdown and links             |
| Automation           | Can be generated from commits/PR labels                                     | Can be auto-generated from changelog or commit history on tagging                |
| Links                | Rich cross-links to PRs, issues, compare ranges                             | Auto-links to commits/PRs; attach downloadable artifacts                         |
| Review in PRs        | Yes—updated alongside code                                                  | Not usually; created at tag time                                                 |
| Offline availability | Yes (bundled in repo/tarball)                                               | No (unless you keep a `RELEASES.md` copy)                                        |
| Best for             | Full, auditable history and contributor workflow                            | Distribution, announcements, and installer-friendly notes                        |


### CHANGELOG.md Sample

```
# Changelog
All notable changes to this project will be documented here.

## [Unreleased]

## [1.4.0] - 2025-09-26
### Added
- New CLI flag `--dry-run`.

### Changed
- Improved sync performance by ~20%.

### Fixed
- Crash on empty config.

### Commits
commits in format 
```
git log --decorate --abbrev=7 \                                                   
  --pretty=format:"%h %d %s%x1f%an%x1f%ad" \
  --date=format:'%Y-%m-%d %H:%M %z' |
gawk -F'\x1f' '{
  # $1 = "hash refs subject", $2 = autor, $3 = fecha
  printf "%-80s\t%s\t%s\n", $1, $2, $3
}'
```
## [1.3.2] - 2025-08-10
### Fixed
- Windows path handling regression.

[Unreleased]: https://github.com/org/repo/compare/v1.4.0...HEAD
[1.4.0]: https://github.com/org/repo/compare/v1.3.2...v1.4.0
```
