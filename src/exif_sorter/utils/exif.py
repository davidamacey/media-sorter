"""Utility for extracting dates from media file EXIF metadata."""

from __future__ import annotations

import logging
import re
from datetime import datetime
from os import path
from typing import Any

from exiftool import ExifToolHelper

# Priority order for date extraction
# CreationDate has timezone info (local time), CreateDate may be UTC
DATE_TAGS: list[str] = [
    # Video (QuickTime container: MP4, MOV, M4V, M4A)
    "QuickTime:CreationDate",  # Has timezone - gives correct local date
    "QuickTime:CreateDate",  # May be UTC - fallback for older videos
    # Images (EXIF)
    "EXIF:DateTimeOriginal",
    "EXIF:CreateDate",
    # Audio - MP3 (ID3 tags)
    "ID3:RecordingTime",  # ID3v2.4 TDRC tag
    "ID3:Year",  # ID3v2.3/v2.4 TYER tag (year only)
    # Audio - WAV (RIFF tags)
    "RIFF:DateTimeOriginal",  # IDIT chunk
    "RIFF:DateCreated",  # ICRD chunk
    # Universal fallback
    "File:FileModifyDate",
]

# AAE sidecar files only have file modification date
AAE_DATE_TAGS: list[str] = ["File:FileModifyDate"]

# Patterns for extracting dates from filenames
# Matches: IMG_20231225_143022, VID_20231225_143022, VN_20231225_143022, etc.
FILENAME_DATE_PATTERNS: list[str] = [
    r"(\d{4})(\d{2})(\d{2})[_-]?(\d{2})(\d{2})(\d{2})",  # 20231225_143022
    r"(\d{4})-(\d{2})-(\d{2})[_T ]?(\d{2}):?(\d{2}):?(\d{2})",  # 2023-12-25_14:30:22
    r"(\d{4})(\d{2})(\d{2})",  # 20231225 (no time)
    r"(\d{4})-(\d{2})-(\d{2})",  # 2023-12-25 (no time)
]


def parse_datetime_from_string(date_str: Any) -> datetime | None:
    """Parse datetime from EXIF date string.

    Args:
        date_str: Date string like '2023:12:25 14:30:22'

    Returns:
        datetime object or None
    """
    if not date_str or len(date_str) < 10:
        return None

    # Extract date portion (first 10 chars): '2023:12:25' -> '2023-12-25'
    date_part = date_str[:10].replace(":", "-")

    # Skip invalid dates
    if date_part == "0000-00-00":
        return None

    # Try to extract time portion
    time_part = "00:00:00"
    if len(date_str) >= 19:
        # '2023:12:25 14:30:22' -> '14:30:22'
        time_part = date_str[11:19]

    try:
        return datetime.strptime(
            f"{date_part} {time_part}", "%Y-%m-%d %H:%M:%S"
        )
    except ValueError:
        try:
            return datetime.strptime(date_part, "%Y-%m-%d")
        except ValueError:
            return None


def extract_date_from_filename(file_path: str) -> datetime | None:
    """Extract date from filename patterns.

    Supports patterns like:
    - IMG_20231225_143022.jpg
    - VID_20231225_143022.mp4
    - 2023-12-25_photo.jpg
    - 20231225.jpg

    Args:
        file_path: Path to file

    Returns:
        datetime object or None
    """
    filename = path.basename(file_path)

    for pattern in FILENAME_DATE_PATTERNS:
        match = re.search(pattern, filename)
        if match:
            groups = match.groups()
            try:
                year, month, day = (
                    int(groups[0]),
                    int(groups[1]),
                    int(groups[2]),
                )

                # Validate date ranges
                if not (
                    1990 <= year <= 2100
                    and 1 <= month <= 12
                    and 1 <= day <= 31
                ):
                    continue

                # Extract time if available
                if len(groups) >= 6:
                    hour, minute, second = (
                        int(groups[3]),
                        int(groups[4]),
                        int(groups[5]),
                    )
                    if (
                        0 <= hour <= 23
                        and 0 <= minute <= 59
                        and 0 <= second <= 59
                    ):
                        return datetime(year, month, day, hour, minute, second)

                return datetime(year, month, day)
            except (ValueError, IndexError):
                continue

    return None


def get_media_date(
    file_path: str, use_filename_fallback: bool = True
) -> datetime | None:
    """Extract creation date from media file metadata.

    Checks multiple EXIF/QuickTime tags in priority order.
    Falls back to filename pattern matching if enabled.

    Args:
        file_path: Path to media file
        use_filename_fallback: Try to extract date from filename if EXIF fails

    Returns:
        datetime object, or None if no date found
    """
    dt: datetime | None = None

    try:
        with ExifToolHelper() as et:
            output: dict[str, Any] = et.get_metadata(file_path)[0]

        # AAE sidecar files have limited tags
        tags_to_check = (
            AAE_DATE_TAGS
            if output.get("File:FileType") == "AAE"
            else DATE_TAGS
        )

        for tag in tags_to_check:
            if tag in output:
                dt = parse_datetime_from_string(output[tag])
                if dt:
                    break

    except Exception as e:
        logging.warning(f"Error reading metadata for {file_path}: {e}")

    # Fallback to filename if no EXIF date found
    if dt is None and use_filename_fallback:
        dt = extract_date_from_filename(file_path)

    return dt
