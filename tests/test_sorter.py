"""Tests for MediaFileSorter class and check_exiftool function."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from media_sorter.sorter import MediaFileSorter, check_exiftool


class TestCheckExiftool:
    """Test check_exiftool function."""

    def test_check_exiftool_success(self, mock_exiftool_success):
        """Test check_exiftool when exiftool is available."""
        version = check_exiftool()
        assert version == "12.50"

    def test_check_exiftool_not_found(self, mock_exiftool_not_found):
        """Test check_exiftool raises error when exiftool not found."""
        with pytest.raises(RuntimeError, match="exiftool is required"):
            check_exiftool()

    def test_check_exiftool_timeout(self, monkeypatch):
        """Test check_exiftool handles timeout."""
        import subprocess

        def mock_run(*args, **kwargs):
            raise subprocess.TimeoutExpired("exiftool", 5)

        monkeypatch.setattr(subprocess, "run", mock_run)

        with pytest.raises(RuntimeError, match="exiftool is required"):
            check_exiftool()


class TestMediaFileSorterInit:
    """Test MediaFileSorter initialization."""

    def test_init_with_valid_directories(
        self, temp_source_dir: Path, temp_dest_dir: Path
    ):
        """Test initialization with valid directories."""
        sorter = MediaFileSorter(str(temp_source_dir), str(temp_dest_dir))
        assert sorter.source_dir == str(temp_source_dir)
        assert sorter.dest_dir == str(temp_dest_dir)
        assert sorter.move_files is True
        assert sorter.dry_run is False
        assert sorter.date_format == "%Y-%m-%d"
        assert sorter.day_begins == 0

    def test_init_creates_dest_dir_if_not_exists(self, temp_source_dir: Path, tmp_path: Path):
        """Test that destination directory can be created."""
        dest_dir = tmp_path / "new_dest"
        sorter = MediaFileSorter(str(temp_source_dir), str(dest_dir))
        assert sorter.dest_dir == str(dest_dir)

    def test_init_with_log_file(
        self, temp_source_dir: Path, temp_dest_dir: Path
    ):
        """Test initialization with log file."""
        sorter = MediaFileSorter(
            str(temp_source_dir), str(temp_dest_dir), "test.log"
        )
        assert sorter.log_file == "test.log"

    def test_init_source_not_exists(self, temp_dest_dir: Path):
        """Test initialization fails when source doesn't exist."""
        with pytest.raises(FileNotFoundError, match="Source directory does not exist"):
            MediaFileSorter("/nonexistent/path", str(temp_dest_dir))

    def test_init_source_not_directory(self, temp_dest_dir: Path, tmp_path: Path):
        """Test initialization fails when source is not a directory."""
        file = tmp_path / "file.txt"
        file.write_text("content")

        with pytest.raises(NotADirectoryError, match="Source is not a directory"):
            MediaFileSorter(str(file), str(temp_dest_dir))

    def test_init_dest_not_writable(
        self, temp_source_dir: Path, temp_dest_dir: Path, monkeypatch
    ):
        """Test initialization fails when destination exists but is not writable."""
        # dest_dir must exist for the check to run
        temp_dest_dir.mkdir(exist_ok=True)

        def mock_access(path, mode):
            return False

        import media_sorter.sorter
        monkeypatch.setattr(media_sorter.sorter, "access", mock_access)

        with pytest.raises(PermissionError, match="not writable"):
            MediaFileSorter(str(temp_source_dir), str(temp_dest_dir))


class TestMediaFileSorterDateLogic:
    """Test MediaFileSorter date-related methods."""

    def test_apply_day_begins_no_adjustment(
        self, temp_source_dir: Path, temp_dest_dir: Path
    ):
        """Test day_begins=0 makes no adjustment."""
        sorter = MediaFileSorter(str(temp_source_dir), str(temp_dest_dir))
        sorter.day_begins = 0

        dt = datetime(2023, 12, 25, 2, 30, 0)
        result = sorter._apply_day_begins(dt)
        assert result == dt

    def test_apply_day_begins_before_cutoff(
        self, temp_source_dir: Path, temp_dest_dir: Path
    ):
        """Test photo before day_begins hour belongs to previous day."""
        sorter = MediaFileSorter(str(temp_source_dir), str(temp_dest_dir))
        sorter.day_begins = 4  # Day starts at 4am

        # Photo at 2am should belong to previous day
        dt = datetime(2023, 12, 25, 2, 30, 0)
        result = sorter._apply_day_begins(dt)
        assert result == datetime(2023, 12, 24, 2, 30, 0)

    def test_apply_day_begins_after_cutoff(
        self, temp_source_dir: Path, temp_dest_dir: Path
    ):
        """Test photo after day_begins hour stays same day."""
        sorter = MediaFileSorter(str(temp_source_dir), str(temp_dest_dir))
        sorter.day_begins = 4  # Day starts at 4am

        # Photo at 5am should stay same day
        dt = datetime(2023, 12, 25, 5, 0, 0)
        result = sorter._apply_day_begins(dt)
        assert result == dt

    def test_apply_day_begins_at_cutoff(
        self, temp_source_dir: Path, temp_dest_dir: Path
    ):
        """Test photo exactly at day_begins hour stays same day."""
        sorter = MediaFileSorter(str(temp_source_dir), str(temp_dest_dir))
        sorter.day_begins = 4

        dt = datetime(2023, 12, 25, 4, 0, 0)
        result = sorter._apply_day_begins(dt)
        assert result == dt

    def test_is_in_date_range_no_filter(
        self, temp_source_dir: Path, temp_dest_dir: Path
    ):
        """Test all dates pass when no filter set."""
        sorter = MediaFileSorter(str(temp_source_dir), str(temp_dest_dir))

        dt = datetime(2023, 12, 25, 14, 30, 0)
        assert sorter._is_in_date_range(dt) is True

    def test_is_in_date_range_from_date(
        self, temp_source_dir: Path, temp_dest_dir: Path
    ):
        """Test from_date filtering."""
        from datetime import date

        sorter = MediaFileSorter(str(temp_source_dir), str(temp_dest_dir))
        sorter.from_date = date(2023, 12, 20)

        # Before from_date
        assert sorter._is_in_date_range(datetime(2023, 12, 19, 10, 0, 0)) is False

        # On from_date
        assert sorter._is_in_date_range(datetime(2023, 12, 20, 10, 0, 0)) is True

        # After from_date
        assert sorter._is_in_date_range(datetime(2023, 12, 25, 10, 0, 0)) is True

    def test_is_in_date_range_to_date(
        self, temp_source_dir: Path, temp_dest_dir: Path
    ):
        """Test to_date filtering."""
        from datetime import date

        sorter = MediaFileSorter(str(temp_source_dir), str(temp_dest_dir))
        sorter.to_date = date(2023, 12, 25)

        # Before to_date
        assert sorter._is_in_date_range(datetime(2023, 12, 20, 10, 0, 0)) is True

        # On to_date
        assert sorter._is_in_date_range(datetime(2023, 12, 25, 10, 0, 0)) is True

        # After to_date
        assert sorter._is_in_date_range(datetime(2023, 12, 26, 10, 0, 0)) is False

    def test_is_in_date_range_both(
        self, temp_source_dir: Path, temp_dest_dir: Path
    ):
        """Test filtering with both from_date and to_date."""
        from datetime import date

        sorter = MediaFileSorter(str(temp_source_dir), str(temp_dest_dir))
        sorter.from_date = date(2023, 12, 20)
        sorter.to_date = date(2023, 12, 25)

        assert sorter._is_in_date_range(datetime(2023, 12, 19, 10, 0, 0)) is False
        assert sorter._is_in_date_range(datetime(2023, 12, 22, 10, 0, 0)) is True
        assert sorter._is_in_date_range(datetime(2023, 12, 26, 10, 0, 0)) is False

    def test_get_folder_name_default_format(
        self, temp_source_dir: Path, temp_dest_dir: Path
    ):
        """Test folder name generation with default format."""
        sorter = MediaFileSorter(str(temp_source_dir), str(temp_dest_dir))

        dt = datetime(2023, 12, 25, 14, 30, 0)
        folder = sorter._get_folder_name(dt)
        assert folder == "2023-12-25"

    def test_get_folder_name_custom_format(
        self, temp_source_dir: Path, temp_dest_dir: Path
    ):
        """Test folder name generation with custom format."""
        sorter = MediaFileSorter(str(temp_source_dir), str(temp_dest_dir))
        sorter.date_format = "%Y/%m/%d"

        dt = datetime(2023, 12, 25, 14, 30, 0)
        folder = sorter._get_folder_name(dt)
        assert folder == "2023/12/25"

    def test_get_folder_name_month_format(
        self, temp_source_dir: Path, temp_dest_dir: Path
    ):
        """Test folder name with month-only format."""
        sorter = MediaFileSorter(str(temp_source_dir), str(temp_dest_dir))
        sorter.date_format = "%Y-%m"

        dt = datetime(2023, 12, 25, 14, 30, 0)
        folder = sorter._get_folder_name(dt)
        assert folder == "2023-12"

    def test_get_folder_name_applies_day_begins(
        self, temp_source_dir: Path, temp_dest_dir: Path
    ):
        """Test folder name respects day_begins adjustment."""
        sorter = MediaFileSorter(str(temp_source_dir), str(temp_dest_dir))
        sorter.day_begins = 4

        # Photo at 2am should use previous day's folder
        dt = datetime(2023, 12, 25, 2, 30, 0)
        folder = sorter._get_folder_name(dt)
        assert folder == "2023-12-24"


class TestMediaFileSorterFileOperations:
    """Test MediaFileSorter file operation methods."""

    def test_create_destination_folders(
        self, temp_source_dir: Path, temp_dest_dir: Path
    ):
        """Test destination folders are created."""
        sorter = MediaFileSorter(str(temp_source_dir), str(temp_dest_dir))
        sorter.create_destination_folders()

        assert Path(temp_dest_dir).exists()
        assert Path(sorter.no_date_folder).exists()
        assert Path(sorter.error_folder).exists()
        assert sorter.no_date_folder.endswith("00_no_date_found")
        assert sorter.error_folder.endswith("00_media_error")

    def test_track_file(self, temp_source_dir: Path, temp_dest_dir: Path):
        """Test file tracking increments counters."""
        sorter = MediaFileSorter(str(temp_source_dir), str(temp_dest_dir))

        sorter._track_file(".jpg")
        sorter._track_file(".jpg")
        sorter._track_file(".mp4")

        assert sorter.total_files_processed == 3
        assert sorter.files_by_type[".jpg"] == 2
        assert sorter.files_by_type[".mp4"] == 1

    def test_handle_dated_file_copy(
        self,
        temp_source_dir: Path,
        temp_dest_dir: Path,
        sample_image_file: Path,
        mock_exiftool_metadata,
    ):
        """Test handling dated file with copy mode."""
        sorter = MediaFileSorter(str(temp_source_dir), str(temp_dest_dir))
        sorter.move_files = False
        sorter.create_destination_folders()

        sorter.process_file(str(sample_image_file))

        # Original file should still exist (copy mode)
        assert sample_image_file.exists()

        # File should be in destination
        dest_file = temp_dest_dir / "2023-12-25" / sample_image_file.name
        assert dest_file.exists()

    def test_handle_dated_file_move(
        self,
        temp_source_dir: Path,
        temp_dest_dir: Path,
        sample_image_file: Path,
        mock_exiftool_metadata,
    ):
        """Test handling dated file with move mode."""
        sorter = MediaFileSorter(str(temp_source_dir), str(temp_dest_dir))
        sorter.move_files = True
        sorter.create_destination_folders()

        sorter.process_file(str(sample_image_file))

        # Original file should not exist (move mode)
        assert not sample_image_file.exists()

        # File should be in destination
        dest_file = temp_dest_dir / "2023-12-25" / sample_image_file.name
        assert dest_file.exists()

    def test_handle_dated_file_dry_run(
        self,
        temp_source_dir: Path,
        temp_dest_dir: Path,
        sample_image_file: Path,
        mock_exiftool_metadata,
    ):
        """Test dry run mode doesn't move files."""
        sorter = MediaFileSorter(str(temp_source_dir), str(temp_dest_dir))
        sorter.dry_run = True
        sorter.create_destination_folders()

        sorter.process_file(str(sample_image_file))

        # Original file should still exist
        assert sample_image_file.exists()

        # Destination folder should not be created
        dest_folder = temp_dest_dir / "2023-12-25"
        assert not dest_folder.exists()

    def test_handle_duplicate_file_same_content(
        self,
        temp_source_dir: Path,
        temp_dest_dir: Path,
        mock_exiftool_metadata,
    ):
        """Test duplicate file with same content is skipped."""
        # Create original file in destination
        dest_folder = temp_dest_dir / "2023-12-25"
        dest_folder.mkdir(parents=True)
        dest_file = dest_folder / "IMG_20231225_143022.jpg"
        dest_file.write_text("fake image data")

        # Create identical file in source
        source_file = temp_source_dir / "IMG_20231225_143022.jpg"
        source_file.write_text("fake image data")

        sorter = MediaFileSorter(str(temp_source_dir), str(temp_dest_dir))
        sorter.move_files = True
        sorter.create_destination_folders()

        sorter.process_file(str(source_file))

        # Source file should be removed (duplicate)
        assert not source_file.exists()

        # Only one file in destination
        assert len(list(dest_folder.glob("*"))) == 1

    def test_handle_duplicate_filename_different_content(
        self,
        temp_source_dir: Path,
        temp_dest_dir: Path,
        mock_exiftool_metadata,
    ):
        """Test duplicate filename with different content is renamed."""
        # Create original file in destination
        dest_folder = temp_dest_dir / "2023-12-25"
        dest_folder.mkdir(parents=True)
        dest_file = dest_folder / "IMG_20231225_143022.jpg"
        dest_file.write_text("original content")

        # Create different file with same name in source
        source_file = temp_source_dir / "IMG_20231225_143022.jpg"
        source_file.write_text("different content")

        sorter = MediaFileSorter(str(temp_source_dir), str(temp_dest_dir))
        sorter.move_files = False
        sorter.create_destination_folders()

        sorter.process_file(str(source_file))

        # Both files should exist in destination
        assert dest_file.exists()
        renamed_file = dest_folder / "IMG_20231225_143022_1.jpg"
        assert renamed_file.exists()

    def test_handle_no_date_file(
        self,
        temp_source_dir: Path,
        temp_dest_dir: Path,
        sample_file_no_date: Path,
        mock_exiftool_no_date,
    ):
        """Test file with no date goes to no_date folder."""
        sorter = MediaFileSorter(str(temp_source_dir), str(temp_dest_dir))
        sorter.move_files = False
        sorter.create_destination_folders()

        sorter.process_file(str(sample_file_no_date))

        # File should be in no_date folder
        dest_file = Path(sorter.no_date_folder) / sample_file_no_date.name
        assert dest_file.exists()
        assert sorter.files_by_type["no_date"] == 1

    def test_handle_error_file(
        self,
        temp_source_dir: Path,
        temp_dest_dir: Path,
        sample_image_file: Path,
        monkeypatch,
    ):
        """Test file that causes processing error goes to error folder."""
        # Mock get_media_date to raise an exception (not just return None)
        def mock_get_media_date(file_path: str, use_filename_fallback: bool = True):
            raise RuntimeError("Simulated processing error")

        import media_sorter.sorter
        monkeypatch.setattr(
            media_sorter.sorter, "get_media_date", mock_get_media_date
        )

        sorter = MediaFileSorter(str(temp_source_dir), str(temp_dest_dir))
        sorter.move_files = False
        sorter.create_destination_folders()

        sorter.process_file(str(sample_image_file))

        # File should be in error folder
        dest_file = Path(sorter.error_folder) / sample_image_file.name
        assert dest_file.exists()
        assert sorter.files_by_type["error"] == 1

    def test_skip_file_outside_date_range(
        self,
        temp_source_dir: Path,
        temp_dest_dir: Path,
        sample_image_file: Path,
        mock_exiftool_metadata,
    ):
        """Test file outside date range is skipped."""
        from datetime import date

        sorter = MediaFileSorter(str(temp_source_dir), str(temp_dest_dir))
        sorter.from_date = date(2024, 1, 1)  # After file date
        sorter.create_destination_folders()

        sorter.process_file(str(sample_image_file))

        # File should not be processed
        assert sorter.skipped_by_date_range == 1
        assert sorter.total_files_processed == 0

    def test_remove_empty_folders(
        self, temp_source_dir: Path, temp_dest_dir: Path
    ):
        """Test removal of empty folders."""
        # Create nested empty folders
        empty1 = temp_source_dir / "empty1"
        empty2 = temp_source_dir / "empty2" / "nested"
        empty1.mkdir()
        empty2.mkdir(parents=True)

        # Create folder with file
        with_file = temp_source_dir / "with_file"
        with_file.mkdir()
        (with_file / "file.txt").write_text("content")

        sorter = MediaFileSorter(str(temp_source_dir), str(temp_dest_dir))
        sorter.remove_empty_folders(str(temp_source_dir))

        # Empty folders should be removed
        assert not empty1.exists()
        assert not empty2.exists()

        # Folder with file should remain
        assert with_file.exists()

        # Source dir itself should remain
        assert temp_source_dir.exists()
