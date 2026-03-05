#!/usr/bin/env python3
"""
duplicate_finder.py — Find and remove duplicate files using SHA-256 hashing.

Usage:
    python duplicate_finder.py /path/to/scan
    python duplicate_finder.py /path/to/scan --dry-run
    python duplicate_finder.py /path/to/scan --auto-delete --min-size 1024
    python duplicate_finder.py /path1 /path2 --output report.txt

Author: https://github.com/nord342
License: MIT
"""

import os
import sys
import hashlib
import argparse
import time
from collections import defaultdict
from pathlib import Path


# ─────────────────────────────────────────────
#  Hashing
# ─────────────────────────────────────────────

def hash_file(filepath: Path, chunk_size: int = 65536) -> str | None:
    """Return SHA-256 hex digest of a file, or None on error."""
    sha256 = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            while chunk := f.read(chunk_size):
                sha256.update(chunk)
        return sha256.hexdigest()
    except (OSError, PermissionError) as e:
        print(f"  [WARN] Cannot read {filepath}: {e}")
        return None


# ─────────────────────────────────────────────
#  Scanning
# ─────────────────────────────────────────────

def scan_directories(paths: list[str], min_size: int = 0,
                     extensions: list[str] | None = None) -> dict[str, list[Path]]:
    """
    Walk all given paths, hash every file that passes filters,
    and return a dict mapping hash → [list of file paths].
    """
    hash_map: dict[str, list[Path]] = defaultdict(list)
    total = 0
    skipped = 0

    ext_filter = {e.lower().lstrip(".") for e in extensions} if extensions else None

    print(f"\nScanning {len(paths)} location(s)…")
    start = time.time()

    for root_path in paths:
        root = Path(root_path).expanduser().resolve()
        if not root.exists():
            print(f"  [ERROR] Path does not exist: {root}")
            continue
        if root.is_file():
            files = [root]
        else:
            files = root.rglob("*")

        for filepath in files:
            if not filepath.is_file():
                continue

            # Extension filter
            if ext_filter and filepath.suffix.lower().lstrip(".") not in ext_filter:
                skipped += 1
                continue

            # Size filter
            try:
                size = filepath.stat().st_size
            except OSError:
                skipped += 1
                continue

            if size < min_size:
                skipped += 1
                continue

            total += 1
            print(f"\r  Files scanned: {total}", end="", flush=True)

            digest = hash_file(filepath)
            if digest:
                hash_map[digest].append(filepath)

    elapsed = time.time() - start
    print(f"\r  Files scanned: {total} in {elapsed:.1f}s (skipped {skipped})")
    return hash_map


# ─────────────────────────────────────────────
#  Reporting
# ─────────────────────────────────────────────

def build_report(hash_map: dict[str, list[Path]]) -> list[list[Path]]:
    """Return only groups that have more than one file (actual duplicates)."""
    return [paths for paths in hash_map.values() if len(paths) > 1]


def human_size(num_bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} PB"


def print_report(groups: list[list[Path]]) -> int:
    """Print duplicate groups and return total wasted bytes."""
    if not groups:
        print("\nNo duplicates found. Your directories are clean!")
        return 0

    total_wasted = 0
    print(f"\nFound {len(groups)} group(s) of duplicate files:\n")
    print("=" * 70)

    for i, group in enumerate(groups, 1):
        size = group[0].stat().st_size
        wasted = size * (len(group) - 1)
        total_wasted += wasted
        print(f"\n[Group {i}]  {len(group)} copies  |  {human_size(size)} each  |  "
              f"wasted: {human_size(wasted)}")
        for j, path in enumerate(group):
            marker = "  KEEP →" if j == 0 else "  DUPE  "
            print(f"  {marker} {path}")

    print("\n" + "=" * 70)
    print(f"Total space recoverable: {human_size(total_wasted)}")
    return total_wasted


def save_report(groups: list[list[Path]], output_path: str) -> None:
    """Write the duplicate report to a text file."""
    with open(output_path, "w") as f:
        f.write("Duplicate File Finder — Report\n")
        f.write("=" * 70 + "\n\n")
        for i, group in enumerate(groups, 1):
            size = group[0].stat().st_size
            f.write(f"[Group {i}]  {len(group)} copies  |  {human_size(size)} each\n")
            for j, path in enumerate(group):
                marker = "KEEP" if j == 0 else "DUPE"
                f.write(f"  [{marker}] {path}\n")
            f.write("\n")
    print(f"\nReport saved to: {output_path}")


# ─────────────────────────────────────────────
#  Deletion
# ─────────────────────────────────────────────

def delete_file(filepath: Path, dry_run: bool = False) -> bool:
    """Delete a file. Returns True on success."""
    if dry_run:
        print(f"  [DRY-RUN] Would delete: {filepath}")
        return True
    try:
        filepath.unlink()
        print(f"  Deleted: {filepath}")
        return True
    except OSError as e:
        print(f"  [ERROR] Could not delete {filepath}: {e}")
        return False


def interactive_delete(groups: list[list[Path]], dry_run: bool = False) -> int:
    """
    Interactively prompt the user for each duplicate group.
    Returns the number of files deleted.
    """
    deleted_count = 0

    for i, group in enumerate(groups, 1):
        size = group[0].stat().st_size
        print(f"\n{'─' * 60}")
        print(f"Group {i}/{len(groups)}  |  {human_size(size)} each")
        for j, path in enumerate(group):
            print(f"  [{j}] {path}")

        print("\nOptions:")
        print("  k  — keep all (skip this group)")
        print("  a  — auto-delete all but the first (oldest path)")
        print("  #  — enter numbers to delete (e.g. 1 2)")
        print("  q  — quit deletion")

        while True:
            choice = input("\nYour choice: ").strip().lower()

            if choice == "q":
                print("Stopping deletion.")
                return deleted_count

            if choice == "k":
                break

            if choice == "a":
                for path in group[1:]:
                    if delete_file(path, dry_run):
                        deleted_count += 1
                break

            # Try to parse numbers
            try:
                indices = [int(x) for x in choice.split()]
                valid = all(0 <= idx < len(group) for idx in indices)
                if not valid:
                    print(f"  Please enter numbers between 0 and {len(group) - 1}.")
                    continue
                for idx in indices:
                    if delete_file(group[idx], dry_run):
                        deleted_count += 1
                break
            except ValueError:
                print("  Invalid input. Try again.")

    return deleted_count


def auto_delete(groups: list[list[Path]], dry_run: bool = False) -> int:
    """Delete all duplicates automatically, keeping the first occurrence."""
    deleted_count = 0
    for group in groups:
        for path in group[1:]:
            if delete_file(path, dry_run):
                deleted_count += 1
    return deleted_count


# ─────────────────────────────────────────────
#  CLI
# ─────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="duplicate_finder",
        description=(
            "Find and remove duplicate files using SHA-256 hashing.\n"
            "By default the script runs in read-only mode — no files are deleted\n"
            "unless you pass --interactive or --auto-delete."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python duplicate_finder.py ~/Downloads
  python duplicate_finder.py ~/Documents --dry-run --interactive
  python duplicate_finder.py ~/Pictures --auto-delete --min-size 102400
  python duplicate_finder.py ~/Music ~/Downloads --ext mp3 flac
  python duplicate_finder.py ~/Desktop --output report.txt
        """,
    )

    parser.add_argument(
        "paths",
        nargs="+",
        metavar="PATH",
        help="One or more directories (or files) to scan.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting anything.",
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Prompt for each duplicate group before deleting.",
    )
    parser.add_argument(
        "--auto-delete",
        action="store_true",
        help="Automatically delete all duplicates, keeping the first occurrence.",
    )
    parser.add_argument(
        "--min-size",
        type=int,
        default=0,
        metavar="BYTES",
        help="Skip files smaller than this size in bytes (default: 0).",
    )
    parser.add_argument(
        "--ext",
        nargs="+",
        metavar="EXT",
        default=None,
        help="Only scan files with these extensions (e.g. --ext jpg png pdf).",
    )
    parser.add_argument(
        "--output", "-o",
        metavar="FILE",
        default=None,
        help="Save a report of duplicates to a text file.",
    )
    return parser.parse_args()


# ─────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────

def main() -> None:
    args = parse_args()

    print("╔══════════════════════════════════════╗")
    print("║   Duplicate File Finder & Remover    ║")
    print("╚══════════════════════════════════════╝")

    if args.dry_run:
        print("  [DRY-RUN MODE] No files will be deleted.\n")

    # Scan
    hash_map = scan_directories(args.paths, min_size=args.min_size, extensions=args.ext)

    # Build duplicate groups
    groups = build_report(hash_map)

    # Print report
    print_report(groups)

    # Optionally save report
    if args.output:
        save_report(groups, args.output)

    if not groups:
        sys.exit(0)

    # Deletion
    deleted = 0
    if args.auto_delete:
        print("\nAuto-deleting duplicates (keeping first occurrence)…")
        deleted = auto_delete(groups, dry_run=args.dry_run)
    elif args.interactive:
        deleted = interactive_delete(groups, dry_run=args.dry_run)
    else:
        print("\nRun with --interactive or --auto-delete to remove duplicates.")
        print("Use --dry-run to preview deletions safely.")

    if deleted:
        action = "Would have deleted" if args.dry_run else "Deleted"
        print(f"\n{action} {deleted} file(s).")

    print("\nDone.")


if __name__ == "__main__":
    main()
