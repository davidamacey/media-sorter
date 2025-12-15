"""Main media file sorter module."""

from __future__ import annotations

import logging
import subprocess
import threading
from datetime import date, datetime, timedelta
from os import W_OK, access, makedirs, path, remove, rmdir, walk
from shutil import copy2, move

from imohash import hashfile
from tqdm.contrib.concurrent import thread_map

from .utils.dsstore import remove_ds_store_files
from .utils.exif import get_media_date


def check_exiftool() -> str:
    """Verify exiftool is installed and accessible."""
    try:
        result = subprocess.run(
            ["exiftool", "-ver"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    raise RuntimeError(
        "exiftool is required but not found. Install with:\n"
        "  Ubuntu/Debian: sudo apt install exiftool\n"
        "  macOS: brew install exiftool\n"
        "  Windows: https://exiftool.org"
    )


class MediaFileSorter:
    """Sort media files into date-based folders using EXIF metadata."""

    source_dir: str
    dest_dir: str
    log_file: str | None
    total_files_processed: int
    files_by_type: dict[str, int]
    skipped_by_date_range: int
    move_files: bool
    dry_run: bool
    date_format: str
    day_begins: int
    from_date: date | None
    to_date: date | None
    no_date_folder: str | None
    error_folder: str | None

    def __init__(
        self, source_dir: str, dest_dir: str, log_file: str | None = None
    ) -> None:
        # Validate source directory
        if not path.exists(source_dir):
            raise FileNotFoundError(
                f"Source directory does not exist: {source_dir}"
            )
        if not path.isdir(source_dir):
            raise NotADirectoryError(
                f"Source is not a directory: {source_dir}"
            )

        # Validate destination is writable (create if needed)
        if path.exists(dest_dir) and not access(dest_dir, W_OK):
            raise PermissionError(
                f"Destination directory is not writable: {dest_dir}"
            )

        self.source_dir = source_dir
        self.dest_dir = dest_dir
        self.log_file = log_file

        self.total_files_processed = 0
        self.files_by_type = {}
        self.skipped_by_date_range = 0

        # Thread safety for concurrent file operations
        self._file_lock = threading.Lock()
        self._counter_lock = threading.Lock()

        # Options
        self.move_files = True  # Move instead of copy (removes source)
        self.dry_run = False
        self.date_format = "%Y-%m-%d"  # Folder naming format
        self.day_begins = 0  # Hour when "day" starts (0-23), e.g., 4 = 4am
        self.from_date = None  # Only process files from this date
        self.to_date = None  # Only process files up to this date

        self.no_date_folder = None
        self.error_folder = None

    def create_destination_folders(self) -> None:
        """Create destination and special folders for edge cases."""
        makedirs(self.dest_dir, exist_ok=True)
        self.no_date_folder = path.join(self.dest_dir, "00_no_date_found")
        makedirs(self.no_date_folder, exist_ok=True)
        self.error_folder = path.join(self.dest_dir, "00_media_error")
        makedirs(self.error_folder, exist_ok=True)

    def _apply_day_begins(self, dt: datetime) -> datetime:
        """Adjust datetime based on day_begins hour.

        If day_begins=4, a photo taken at 2am belongs to the previous day.
        """
        if self.day_begins > 0 and dt.hour < self.day_begins:
            return dt - timedelta(days=1)
        return dt

    def _is_in_date_range(self, dt: datetime) -> bool:
        """Check if datetime is within the configured date range."""
        if self.from_date and dt.date() < self.from_date:
            return False
        return not (self.to_date and dt.date() > self.to_date)

    def _get_folder_name(self, dt: datetime) -> str:
        """Generate folder name from datetime using configured format."""
        adjusted_dt = self._apply_day_begins(dt)
        return adjusted_dt.strftime(self.date_format)

    def process_file(self, file: str) -> None:
        """Process a single media file - extract date and move/copy."""
        try:
            dt = get_media_date(file)

            if dt:
                # Check date range filter
                if not self._is_in_date_range(dt):
                    with self._counter_lock:
                        self.skipped_by_date_range += 1
                    return

                folder_name = self._get_folder_name(dt)
                self._handle_dated_file(file, folder_name)
            else:
                self._handle_no_date_file(file)
        except Exception as e:
            self._handle_error_file(file, e)

    def _handle_dated_file(self, file: str, folder_name: str) -> None:
        """Handle a file with a valid date."""
        dest_folder = path.join(self.dest_dir, folder_name)
        if not self.dry_run:
            makedirs(dest_folder, exist_ok=True)

        current_folder = path.dirname(file)
        base_name, ext = path.splitext(path.basename(file))

        # Skip if already in correct folder
        if current_folder == dest_folder:
            return

        # Compute hash once before locking
        new_file_hash: str = hashfile(file, hexdigest=True)

        # Lock for thread-safe file existence check and move/copy
        with self._file_lock:
            dest_file = path.join(dest_folder, path.basename(file))
            counter = 1

            while path.exists(dest_file):
                existing_hash: str = hashfile(dest_file, hexdigest=True)

                if new_file_hash != existing_hash:
                    dest_file = path.join(
                        dest_folder, f"{base_name}_{counter}{ext}"
                    )
                    counter += 1
                else:
                    # File already exists with same content
                    logging.info(f"Duplicate exists: {folder_name} {file}")
                    if self.move_files:
                        remove(file)
                    return

            if not self.dry_run:
                if self.move_files:
                    move(file, dest_file)
                else:
                    copy2(file, dest_file)

        self._track_file(ext)

    def _handle_no_date_file(self, file: str) -> None:
        """Handle a file with no extractable date."""
        assert self.no_date_folder is not None
        base_name, ext = path.splitext(path.basename(file))

        # Lock for thread-safe file existence check and move/copy
        with self._file_lock:
            dest_file = path.join(self.no_date_folder, path.basename(file))

            # Handle duplicate filenames in no_date folder
            counter = 1
            while path.exists(dest_file):
                dest_file = path.join(
                    self.no_date_folder, f"{base_name}_{counter}{ext}"
                )
                counter += 1

            if not self.dry_run:
                if self.move_files:
                    move(file, dest_file)
                else:
                    copy2(file, dest_file)

        self._track_file("no_date")
        logging.info(f"NO DATE: {file}")

    def _handle_error_file(self, file: str, error: Exception) -> None:
        """Handle a file that caused an error during processing."""
        assert self.error_folder is not None
        base_name, ext = path.splitext(path.basename(file))

        # Lock for thread-safe file existence check and move/copy
        with self._file_lock:
            dest_file = path.join(self.error_folder, path.basename(file))

            # Handle duplicate filenames in error folder
            counter = 1
            while path.exists(dest_file):
                dest_file = path.join(
                    self.error_folder, f"{base_name}_{counter}{ext}"
                )
                counter += 1

            if not self.dry_run:
                if self.move_files:
                    move(file, dest_file)
                else:
                    copy2(file, dest_file)

        self._track_file("error")
        logging.error(f"Error processing {file}: {error!s}")

    def _track_file(self, ext: str) -> None:
        """Track processed file counts by extension (thread-safe)."""
        with self._counter_lock:
            self.total_files_processed += 1
            self.files_by_type[ext] = self.files_by_type.get(ext, 0) + 1

    def remove_empty_folders(self, directory: str) -> None:
        """Remove empty directories in a directory tree (leaf dirs only)."""
        print(f"Checking for empty folders in: {directory}")

        # Walk bottom-up to remove nested empty dirs properly
        empty_dirs: list[str] = []
        for dirpath, dirnames, filenames in walk(directory, topdown=False):
            if not dirnames and not filenames and dirpath != directory:
                empty_dirs.append(dirpath)

        for dir_path in empty_dirs:
            try:
                rmdir(dir_path)  # Only removes leaf directory, not parents
                print(f"Removed empty directory: {dir_path}")
            except OSError:
                pass  # Directory not empty or already removed

    def sort(self) -> None:
        """Sort all media files from source to destination."""
        self.create_destination_folders()

        # Clean .DS_Store files from source before processing
        if not self.dry_run:
            print("Cleaning .DS_Store files from source...")
            remove_ds_store_files(self.source_dir, verbose=False)

        # Find all non-hidden files
        media_files = [
            path.join(root, filename)
            for root, _, files in walk(self.source_dir)
            for filename in files
            if not filename.startswith(".")
        ]

        print(f"Found {len(media_files)} files to process")

        if self.dry_run:
            print("[DRY RUN] No files will be moved")

        if self.from_date or self.to_date:
            date_range = []
            if self.from_date:
                date_range.append(f"from {self.from_date}")
            if self.to_date:
                date_range.append(f"to {self.to_date}")
            print(f"Date filter: {' '.join(date_range)}")

        if self.day_begins > 0:
            print(
                f"Day begins at: {self.day_begins}:00 (earlier hours count as previous day)"
            )

        thread_map(self.process_file, media_files)

        # Write summary log
        if self.log_file:
            with open(self.log_file, "w") as log:
                log.write(
                    f"Total Files Processed: {self.total_files_processed}\n"
                )
                if self.skipped_by_date_range > 0:
                    log.write(
                        f"Skipped (outside date range): {self.skipped_by_date_range}\n"
                    )
                for ext, count in self.files_by_type.items():
                    log.write(f"Files with Extension {ext}: {count}\n")
            print(f"Log written to '{self.log_file}'")

        print(f"Media files sorted into '{self.dest_dir}'")
        if self.skipped_by_date_range > 0:
            print(
                f"Skipped {self.skipped_by_date_range} files outside date range"
            )

        # Clean up empty source folders
        if self.move_files and not self.dry_run:
            self.remove_empty_folders(self.source_dir)
