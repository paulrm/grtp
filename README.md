# Version and Release

create script python that helps to manage version and release of a project

The script finds the highest version across all files, increments it,
and then updates all files with the new version to ensure consistency.

v-and-r -v or --view (default)                  | show the current version of the files and show the higest 
v-and-r -p or --patch                           | increase the patch number in the files
v-and-r -mi or --minor                          | increase the minor number in the files
v-and-r -ma or --major                          | increase the major number in the files
v-and-r -r or --release-info                    | generates version.json and shows release notes
v-and-r -rd or --release-diff tag1 tag2         | shows commits only between t1 and t2
v-and-r -rl or --release-last                   | shows commits after last tag to HEAD (no version.json update)
v-and-r -rp or --release-prepate                | prepares the release by updating the version.json file, 
                                                | Create or update CHANGELOG.md and RELEASES.md files
v-and-r -h  or --help                           | Display help information



 VERSION_FILES array with:
   - file: path to the file (supports wildcards like *.py or directory/*.py)
   - pattern: regex pattern to match the version (with the version in the first capture group)
   - template: string template to format the replacement with {version} placeholder

Sample

# Define files to update with their version patterns
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


