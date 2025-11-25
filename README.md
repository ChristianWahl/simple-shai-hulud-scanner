# simple-shai-hulud-scanner

A lightweight detection tool that checks local JavaScript/TypeScript projects for known indicators related to the Shai-Hulud supply-chain compromise.
The scanner retrieves the latest IOC list from the public Wiz repository and compares it against your `package-lock.json` or `yarn.lock`.

## Features

- Downloads the newest IOC package list directly from GitHub
- Parses `package-lock.json` and `yarn.lock`
- Detects compromised or suspicious package versions
- Outputs findings **only** when matches are identified
- Read-only operation: no modifications, no uploads, no side effects

## Installation

```bash
pip install -r requirements.txt
````

## Usage

### Single Scan

```bash
python scanner.py <package-lock.json | yarn.lock>
```

### Recursive Scan Across Many Repositories

Use the included script scan-folder.sh to automatically scan all Git repositories under a directory:

```bash
./scan-folder.sh /path/to/directory
```

It will:

- discover repositories by locating .git/ folders
- detect the available lockfile
- run the scanner
- log all findings to scan-results.log