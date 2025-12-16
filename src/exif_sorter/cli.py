"""Command-line interface for exif-sorter."""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date, datetime

from . import __version__


def setup_logging(log_file: str | None = None) -> None:
    """Configure logging once for the application."""
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stderr)]
    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )


def parse_date(date_str: str) -> date:
    """Parse date string in YYYY-MM-DD format."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError as err:
        raise argparse.ArgumentTypeError(
            f"Invalid date: {date_str}. Use YYYY-MM-DD format."
        ) from err


def confirm_action(message: str, skip_confirm: bool = False) -> bool:
    """Prompt user for confirmation. Returns True if confirmed."""
    if skip_confirm:
        return True
    try:
        response = input(f"{message} [y/N]: ").strip().lower()
        return response in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        print("\nAborted.")
        return False


def cmd_sort(args: argparse.Namespace) -> None:
    """Sort media files by EXIF date."""
    from .sorter import MediaFileSorter, check_exiftool

    # Verify exiftool is available
    check_exiftool()

    # Confirm destructive move operation
    if (
        not args.copy
        and not args.dry_run
        and not confirm_action(
            f"This will MOVE files from '{args.source}' to '{args.dest}' "
            "(source files will be deleted). Continue?",
            skip_confirm=args.yes,
        )
    ):
        print("Aborted.")
        sys.exit(0)

    setup_logging(args.log_file)

    sorter = MediaFileSorter(args.source, args.dest, args.log_file)
    sorter.move_files = not args.copy
    sorter.dry_run = args.dry_run
    sorter.date_format = args.format
    sorter.day_begins = args.day_begins
    sorter.from_date = args.from_date
    sorter.to_date = args.to_date
    sorter.sort()


def cmd_clean(args: argparse.Namespace) -> None:
    """Remove .DS_Store files."""
    from .utils.dsstore import remove_ds_store_files

    remove_ds_store_files(args.directory, verbose=True)


def cmd_dedup(args: argparse.Namespace) -> None:
    """Remove duplicate files."""
    from .utils.duplicates import remove_duplicates_in_directory

    # Confirm destructive delete operation
    if not args.dry_run and not confirm_action(
        f"This will DELETE duplicate files in '{args.directory}'. Continue?",
        skip_confirm=args.yes,
    ):
        print("Aborted.")
        sys.exit(0)

    log_file = args.log_file or "dedup.log"
    setup_logging(log_file)

    total = remove_duplicates_in_directory(
        args.directory, dry_run=args.dry_run, verbose=True
    )
    print(
        f"\n{'Would remove' if args.dry_run else 'Removed'} {total} duplicate files"
    )


def main() -> None:
    """Main entry point for exif-sorter CLI."""
    parser = argparse.ArgumentParser(
        prog="exif-sorter",
        description="Organize photos and videos by EXIF creation date",
    )
    parser.add_argument(
        "--version", "-V", action="version", version=f"%(prog)s {__version__}"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Sort command
    sort_parser = subparsers.add_parser(
        "sort", help="Sort media files into date-based folders"
    )
    sort_parser.add_argument(
        "source", help="Source directory with unsorted media"
    )
    sort_parser.add_argument(
        "dest", help="Destination directory for sorted files"
    )
    sort_parser.add_argument(
        "--log-file",
        "-l",
        default=f"sort_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.log",
        help="Log file path (default: sort_YYYY-MM-DD_HHMMSS.log)",
    )
    sort_parser.add_argument(
        "--copy",
        "-c",
        action="store_true",
        help="Copy files instead of moving (keeps source files)",
    )
    sort_parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Show what would be done without making changes",
    )
    sort_parser.add_argument(
        "--format",
        "-f",
        default="%Y-%m-%d",
        help="Folder name format using strftime (default: %%Y-%%m-%%d). Examples: %%Y/%%m/%%d, %%Y-%%m, %%Y/%%B",
    )
    sort_parser.add_argument(
        "--day-begins",
        type=int,
        default=0,
        choices=range(0, 24),
        metavar="HOUR",
        help='Hour when "day" starts (0-23). Photos before this hour belong to previous day. Useful for events.',
    )
    sort_parser.add_argument(
        "--from-date",
        type=parse_date,
        help="Only process files from this date (YYYY-MM-DD)",
    )
    sort_parser.add_argument(
        "--to-date",
        type=parse_date,
        help="Only process files up to this date (YYYY-MM-DD)",
    )
    sort_parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip confirmation prompt for destructive operations",
    )
    sort_parser.set_defaults(func=cmd_sort)

    # Clean command
    clean_parser = subparsers.add_parser(
        "clean", help="Remove .DS_Store files from a directory"
    )
    clean_parser.add_argument("directory", help="Directory to clean")
    clean_parser.set_defaults(func=cmd_clean)

    # Dedup command
    dedup_parser = subparsers.add_parser(
        "dedup", help="Remove duplicate files within subdirectories"
    )
    dedup_parser.add_argument("directory", help="Directory to deduplicate")
    dedup_parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Show what would be removed without deleting",
    )
    dedup_parser.add_argument(
        "--log-file", "-l", help="Log file path (default: dedup.log)"
    )
    dedup_parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip confirmation prompt for destructive operations",
    )
    dedup_parser.set_defaults(func=cmd_dedup)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
