"""Tests for EXIF date extraction utilities."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from exif_sorter.utils.exif import (
    extract_date_from_filename,
    get_media_date,
    parse_datetime_from_string,
)


class TestParseDatetimeFromString:
    """Test parse_datetime_from_string function."""

    def test_parse_standard_exif_date(self):
        """Test parsing standard EXIF date format."""
        result = parse_datetime_from_string("2023:12:25 14:30:22")
        assert result == datetime(2023, 12, 25, 14, 30, 22)

    def test_parse_date_only(self):
        """Test parsing date without time."""
        result = parse_datetime_from_string("2023:12:25")
        assert result == datetime(2023, 12, 25, 0, 0, 0)

    def test_parse_with_colons_in_date(self):
        """Test parsing with colons in date part."""
        result = parse_datetime_from_string("2023:12:25 14:30:22")
        assert result == datetime(2023, 12, 25, 14, 30, 22)

    def test_parse_with_hyphens_in_date(self):
        """Test parsing with hyphens already in date."""
        result = parse_datetime_from_string("2023-12-25 14:30:22")
        assert result == datetime(2023, 12, 25, 14, 30, 22)

    def test_parse_short_string_returns_none(self):
        """Test that short strings return None."""
        assert parse_datetime_from_string("2023") is None
        assert parse_datetime_from_string("123") is None

    def test_parse_none_returns_none(self):
        """Test that None returns None."""
        assert parse_datetime_from_string(None) is None

    def test_parse_empty_string_returns_none(self):
        """Test that empty string returns None."""
        assert parse_datetime_from_string("") is None

    def test_parse_zero_date_returns_none(self):
        """Test that 0000-00-00 date returns None."""
        assert parse_datetime_from_string("0000:00:00 00:00:00") is None
        assert parse_datetime_from_string("0000-00-00") is None

    def test_parse_invalid_date_returns_none(self):
        """Test that invalid dates return None."""
        assert parse_datetime_from_string("2023:13:45 14:30:22") is None
        assert parse_datetime_from_string("2023:12:99 14:30:22") is None
        assert parse_datetime_from_string("invalid") is None

    def test_parse_malformed_string_returns_none(self):
        """Test that malformed strings return None."""
        assert parse_datetime_from_string("not a date at all") is None
        assert parse_datetime_from_string("2023-12-XX 14:30:22") is None

    def test_parse_with_milliseconds(self):
        """Test parsing date with milliseconds (should ignore them)."""
        result = parse_datetime_from_string("2023:12:25 14:30:22.123")
        assert result == datetime(2023, 12, 25, 14, 30, 22)

    @pytest.mark.parametrize(
        "date_str,expected",
        [
            ("2023:12:25 14:30:22", datetime(2023, 12, 25, 14, 30, 22)),
            ("2023:01:01 00:00:00", datetime(2023, 1, 1, 0, 0, 0)),
            ("2023:12:31 23:59:59", datetime(2023, 12, 31, 23, 59, 59)),
            (
                "2020:02:29 12:00:00",
                datetime(2020, 2, 29, 12, 0, 0),
            ),  # Leap year
        ],
    )
    def test_parse_various_valid_dates(
        self, date_str: str, expected: datetime
    ):
        """Test parsing various valid date formats."""
        result = parse_datetime_from_string(date_str)
        assert result == expected


class TestExtractDateFromFilename:
    """Test extract_date_from_filename function."""

    def test_extract_img_pattern_with_time(self):
        """Test extracting date from IMG_20231225_143022.jpg pattern."""
        result = extract_date_from_filename("IMG_20231225_143022.jpg")
        assert result == datetime(2023, 12, 25, 14, 30, 22)

    def test_extract_vid_pattern_with_time(self):
        """Test extracting date from VID_20231225_153045.mp4 pattern."""
        result = extract_date_from_filename("VID_20231225_153045.mp4")
        assert result == datetime(2023, 12, 25, 15, 30, 45)

    def test_extract_vn_pattern_with_time(self):
        """Test extracting date from VN_20231225_143022.m4a pattern."""
        result = extract_date_from_filename("VN_20231225_143022.m4a")
        assert result == datetime(2023, 12, 25, 14, 30, 22)

    def test_extract_date_only_pattern(self):
        """Test extracting date without time (20231225.jpg)."""
        result = extract_date_from_filename("20231225.jpg")
        assert result == datetime(2023, 12, 25, 0, 0, 0)

    def test_extract_iso_date_pattern(self):
        """Test extracting ISO date format (2023-12-25_photo.jpg)."""
        result = extract_date_from_filename("2023-12-25_photo.jpg")
        assert result == datetime(2023, 12, 25, 0, 0, 0)

    def test_extract_iso_datetime_pattern(self):
        """Test extracting ISO datetime format."""
        result = extract_date_from_filename("2023-12-25_14:30:22.jpg")
        assert result == datetime(2023, 12, 25, 14, 30, 22)

    def test_extract_with_path(self):
        """Test extracting from full path."""
        result = extract_date_from_filename("/path/to/IMG_20231225_143022.jpg")
        assert result == datetime(2023, 12, 25, 14, 30, 22)

    def test_extract_no_date_in_filename(self):
        """Test filename with no date pattern returns None."""
        assert extract_date_from_filename("random_photo.jpg") is None
        assert extract_date_from_filename("no_date_here.mp4") is None

    def test_extract_invalid_date_returns_none(self):
        """Test invalid dates return None."""
        assert extract_date_from_filename("IMG_20231332_143022.jpg") is None
        assert extract_date_from_filename("IMG_20230001_143022.jpg") is None

    def test_extract_out_of_range_year_returns_none(self):
        """Test year out of range returns None."""
        assert extract_date_from_filename("IMG_19891225_143022.jpg") is None
        assert extract_date_from_filename("IMG_21011225_143022.jpg") is None

    def test_extract_invalid_time_returns_date_only(self):
        """Test invalid time returns date without time."""
        result = extract_date_from_filename("IMG_20231225_999999.jpg")
        assert result == datetime(2023, 12, 25, 0, 0, 0)

    @pytest.mark.parametrize(
        "filename,expected",
        [
            ("IMG_20231225_143022.jpg", datetime(2023, 12, 25, 14, 30, 22)),
            ("VID_20231225_120000.mp4", datetime(2023, 12, 25, 12, 0, 0)),
            ("VN_20231225_090000.m4a", datetime(2023, 12, 25, 9, 0, 0)),
            ("2023-12-25_photo.jpg", datetime(2023, 12, 25, 0, 0, 0)),
            ("20231225.png", datetime(2023, 12, 25, 0, 0, 0)),
            ("Photo_20231225.jpg", datetime(2023, 12, 25, 0, 0, 0)),
            ("2023-12-25T14:30:22.jpg", datetime(2023, 12, 25, 14, 30, 22)),
        ],
    )
    def test_extract_various_patterns(self, filename: str, expected: datetime):
        """Test extracting dates from various filename patterns."""
        result = extract_date_from_filename(filename)
        assert result == expected


class TestGetMediaDate:
    """Test get_media_date function."""

    def test_get_date_from_exif(
        self, mock_exiftool_metadata, sample_image_file: Path
    ):
        """Test extracting date from EXIF metadata."""
        result = get_media_date(str(sample_image_file))
        assert result == datetime(2023, 12, 25, 14, 30, 22)

    def test_get_date_fallback_to_filename(
        self, mock_exiftool_no_date, sample_image_file: Path
    ):
        """Test fallback to filename when EXIF has no date."""
        result = get_media_date(str(sample_image_file))
        assert result == datetime(2023, 12, 25, 14, 30, 22)

    def test_get_date_no_fallback(
        self, mock_exiftool_no_date, sample_file_no_date: Path
    ):
        """Test no date found when EXIF and filename both fail."""
        result = get_media_date(str(sample_file_no_date))
        assert result is None

    def test_get_date_disable_filename_fallback(
        self, mock_exiftool_no_date, sample_image_file: Path
    ):
        """Test disabling filename fallback."""
        result = get_media_date(
            str(sample_image_file), use_filename_fallback=False
        )
        assert result is None

    def test_get_date_exiftool_error_uses_fallback(
        self, mock_exiftool_error, sample_image_file: Path
    ):
        """Test fallback to filename when ExifTool raises error."""
        result = get_media_date(str(sample_image_file))
        assert result == datetime(2023, 12, 25, 14, 30, 22)

    def test_get_date_prefers_exif_over_filename(
        self, monkeypatch, sample_image_file: Path
    ):
        """Test that EXIF date is preferred over filename date."""

        # Mock ExifTool to return a different date than filename
        class MockExifToolHelper:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def get_metadata(self, file_path: str):
                return [{"EXIF:DateTimeOriginal": "2024:01:01 10:00:00"}]

        import exif_sorter.utils.exif

        monkeypatch.setattr(
            exif_sorter.utils.exif, "ExifToolHelper", MockExifToolHelper
        )

        result = get_media_date(str(sample_image_file))
        # Should use EXIF date (2024-01-01) not filename date (2023-12-25)
        assert result == datetime(2024, 1, 1, 10, 0, 0)

    def test_get_date_aae_file(self, monkeypatch, temp_source_dir: Path):
        """Test getting date from AAE sidecar file."""
        aae_file = temp_source_dir / "photo.AAE"
        aae_file.write_text("aae content")

        class MockExifToolHelper:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def get_metadata(self, file_path: str):
                return [
                    {
                        "File:FileType": "AAE",
                        "File:FileModifyDate": "2023:12:25 14:30:22",
                    }
                ]

        import exif_sorter.utils.exif

        monkeypatch.setattr(
            exif_sorter.utils.exif, "ExifToolHelper", MockExifToolHelper
        )

        result = get_media_date(str(aae_file))
        assert result == datetime(2023, 12, 25, 14, 30, 22)
