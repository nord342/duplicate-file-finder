# Duplicate File Finder & Remover

> A fast, interactive command-line tool to find and safely remove duplicate files — free up disk space in seconds.

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)]()

---

## Features

- **SHA-256 hashing** — 100% accurate duplicate detection, no false positives
- **Recursive scanning** — scans entire folder trees automatically
- **Multi-directory support** — scan multiple folders in one run
- **Interactive mode** — choose exactly which duplicates to delete, one group at a time
- **Auto-delete mode** — hands-free removal keeping the first occurrence
- **Dry-run mode** — safely preview what *would* be deleted before committing
- **Filter by extension** — only scan specific file types (e.g. jpg, mp3, pdf)
- **Minimum size filter** — skip small files below a threshold
- **Report export** — save a full list of duplicates to a text file
- **Zero dependencies** — uses Python standard library only

---

## Quick Start

```bash
# Clone the repo
git clone https://github.com/nord342/duplicate-file-finder.git
cd duplicate-file-finder

# Run a scan (read-only, safe)
python duplicate_finder.py ~/Downloads

# Preview what would be deleted (dry-run)
python duplicate_finder.py ~/Downloads --dry-run --interactive

# Auto-delete all duplicates (keeps first file found)
python duplicate_finder.py ~/Downloads --auto-delete
```

---

## Requirements

- Python **3.10 or higher**
- No third-party packages needed

---

## Usage

```
python duplicate_finder.py PATH [PATH ...] [OPTIONS]
```

### Arguments

| Argument | Description |
|---|---|
| `PATH` | One or more directories or files to scan |

### Options

| Flag | Description |
|---|---|
| `--dry-run` | Preview deletions without removing anything |
| `--interactive`, `-i` | Prompt before deleting each group of duplicates |
| `--auto-delete` | Automatically delete duplicates, keeping first occurrence |
| `--min-size BYTES` | Skip files smaller than N bytes (default: 0) |
| `--ext EXT [EXT ...]` | Only scan files with these extensions |
| `--output FILE`, `-o FILE` | Save duplicate report to a text file |

---

## Examples

```bash
# Scan a single folder
python duplicate_finder.py ~/Pictures

# Scan multiple folders at once
python duplicate_finder.py ~/Downloads ~/Desktop ~/Documents

# Only look at images
python duplicate_finder.py ~/Pictures --ext jpg jpeg png gif webp

# Skip files smaller than 1 MB
python duplicate_finder.py ~/Downloads --min-size 1048576

# Interactive deletion — choose what to keep
python duplicate_finder.py ~/Downloads --interactive

# Safe preview with a saved report
python duplicate_finder.py ~/Downloads --dry-run --output duplicates_report.txt

# Fully automatic cleanup
python duplicate_finder.py ~/Downloads --auto-delete
```

---

## How It Works

1. All files in the target directories are **hashed** using SHA-256
2. Files sharing the same hash are **exact duplicates** (same content, regardless of filename)
3. Duplicate groups are displayed with file sizes and recoverable space shown
4. You choose to delete interactively, automatically, or just view the report

---

## Interactive Mode Walkthrough

```
────────────────────────────────────────────────────
Group 1/3  |  4.2 MB each
  [0] /Users/you/Downloads/holiday_photo.jpg
  [1] /Users/you/Desktop/Copy of holiday_photo.jpg
  [2] /Users/you/Documents/holiday_photo.jpg

Options:
  k  — keep all (skip this group)
  a  — auto-delete all but the first
  #  — enter numbers to delete (e.g. 1 2)
  q  — quit deletion
```

---

## Safety Notes

- By default the script is **completely read-only** — it only reports duplicates
- Use `--dry-run` to preview before any real deletion
- The script never deletes the **first** file in a group automatically
- Always back up important data before bulk-deleting files

---

## Contributing

Pull requests and issues are welcome! If you find a bug or have a feature idea, please [open an issue](../../issues).

---

## License

MIT © [nord342](https://github.com/nord342)
