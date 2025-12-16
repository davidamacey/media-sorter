"""Tests for CLI argument parsing and commands."""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from exif_sorter import __version__
from exif_sorter.cli import (
    cmd_clean,
    cmd_dedup,
    cmd_sort,
    confirm_action,
    main,
    parse_date,
)


class TestParseDate:
    """Test parse_date function."""

    def test_parse_valid_date(self):
        """Test parsing valid date string."""
        result = parse_date("2023-12-25")
        assert result == date(2023, 12, 25)

    def test_parse_leap_year(self):
        """Test parsing leap year date."""
        result = parse_date("2020-02-29")
        assert result == date(2020, 2, 29)

    def test_parse_invalid_format(self):
        """Test parsing invalid format raises error."""
        with pytest.raises(argparse.ArgumentTypeError, match="Invalid date"):
            parse_date("25-12-2023")

    def test_parse_invalid_date(self):
        """Test parsing invalid date raises error."""
        with pytest.raises(argparse.ArgumentTypeError, match="Invalid date"):
            parse_date("2023-13-01")

    def test_parse_invalid_day(self):
        """Test parsing invalid day raises error."""
        with pytest.raises(argparse.ArgumentTypeError, match="Invalid date"):
            parse_date("2023-02-30")

    def test_parse_wrong_separator(self):
        """Test parsing with wrong separator raises error."""
        with pytest.raises(argparse.ArgumentTypeError, match="Invalid date"):
            parse_date("2023/12/25")

    @pytest.mark.parametrize(
        "date_str,expected",
        [
            ("2023-12-25", date(2023, 12, 25)),
            ("2023-01-01", date(2023, 1, 1)),
            ("2023-12-31", date(2023, 12, 31)),
            ("2020-02-29", date(2020, 2, 29)),
        ],
    )
    def test_parse_various_dates(self, date_str: str, expected: date):
        """Test parsing various valid dates."""
        result = parse_date(date_str)
        assert result == expected


class TestConfirmAction:
    """Test confirm_action function."""

    def test_confirm_yes(self, monkeypatch):
        """Test confirmation with 'yes' input."""
        monkeypatch.setattr("builtins.input", lambda _: "yes")
        assert confirm_action("Continue?") is True

    def test_confirm_y(self, monkeypatch):
        """Test confirmation with 'y' input."""
        monkeypatch.setattr("builtins.input", lambda _: "y")
        assert confirm_action("Continue?") is True

    def test_confirm_no(self, monkeypatch):
        """Test confirmation with 'no' input."""
        monkeypatch.setattr("builtins.input", lambda _: "no")
        assert confirm_action("Continue?") is False

    def test_confirm_n(self, monkeypatch):
        """Test confirmation with 'n' input."""
        monkeypatch.setattr("builtins.input", lambda _: "n")
        assert confirm_action("Continue?") is False

    def test_confirm_empty(self, monkeypatch):
        """Test confirmation with empty input defaults to no."""
        monkeypatch.setattr("builtins.input", lambda _: "")
        assert confirm_action("Continue?") is False

    def test_confirm_skip(self):
        """Test confirmation with skip_confirm=True."""
        assert confirm_action("Continue?", skip_confirm=True) is True

    def test_confirm_eof(self, monkeypatch):
        """Test confirmation handles EOF."""

        def raise_eof(_):
            raise EOFError

        monkeypatch.setattr("builtins.input", raise_eof)
        assert confirm_action("Continue?") is False

    def test_confirm_keyboard_interrupt(self, monkeypatch):
        """Test confirmation handles keyboard interrupt."""

        def raise_interrupt(_):
            raise KeyboardInterrupt

        monkeypatch.setattr("builtins.input", raise_interrupt)
        assert confirm_action("Continue?") is False


class TestCmdSort:
    """Test cmd_sort function."""

    def test_cmd_sort_with_copy(
        self,
        temp_source_dir: Path,
        temp_dest_dir: Path,
        mock_exiftool_success,
        monkeypatch,
    ):
        """Test sort command with copy mode."""
        args = argparse.Namespace(
            source=str(temp_source_dir),
            dest=str(temp_dest_dir),
            log_file="test.log",
            copy=True,
            dry_run=False,
            format="%Y-%m-%d",
            day_begins=0,
            from_date=None,
            to_date=None,
            yes=False,
        )

        # Mock the sorter
        mock_sorter = MagicMock()
        with patch(
            "exif_sorter.sorter.MediaFileSorter", return_value=mock_sorter
        ):
            cmd_sort(args)

        assert mock_sorter.move_files is False
        assert mock_sorter.dry_run is False
        mock_sorter.sort.assert_called_once()

    def test_cmd_sort_with_move_confirmed(
        self,
        temp_source_dir: Path,
        temp_dest_dir: Path,
        mock_exiftool_success,
        monkeypatch,
    ):
        """Test sort command with move mode (confirmed)."""
        monkeypatch.setattr("builtins.input", lambda _: "yes")

        args = argparse.Namespace(
            source=str(temp_source_dir),
            dest=str(temp_dest_dir),
            log_file="test.log",
            copy=False,
            dry_run=False,
            format="%Y-%m-%d",
            day_begins=0,
            from_date=None,
            to_date=None,
            yes=False,
        )

        mock_sorter = MagicMock()
        with patch(
            "exif_sorter.sorter.MediaFileSorter", return_value=mock_sorter
        ):
            cmd_sort(args)

        assert mock_sorter.move_files is True
        mock_sorter.sort.assert_called_once()

    def test_cmd_sort_with_move_declined(
        self,
        temp_source_dir: Path,
        temp_dest_dir: Path,
        mock_exiftool_success,
        monkeypatch,
    ):
        """Test sort command with move mode (declined)."""
        monkeypatch.setattr("builtins.input", lambda _: "no")

        args = argparse.Namespace(
            source=str(temp_source_dir),
            dest=str(temp_dest_dir),
            log_file="test.log",
            copy=False,
            dry_run=False,
            format="%Y-%m-%d",
            day_begins=0,
            from_date=None,
            to_date=None,
            yes=False,
        )

        mock_sorter = MagicMock()
        with (
            patch(
                "exif_sorter.sorter.MediaFileSorter", return_value=mock_sorter
            ),
            pytest.raises(SystemExit),
        ):
            cmd_sort(args)

        # Sorter should not be called
        mock_sorter.sort.assert_not_called()

    def test_cmd_sort_with_yes_flag(
        self,
        temp_source_dir: Path,
        temp_dest_dir: Path,
        mock_exiftool_success,
    ):
        """Test sort command with --yes flag skips confirmation."""
        args = argparse.Namespace(
            source=str(temp_source_dir),
            dest=str(temp_dest_dir),
            log_file="test.log",
            copy=False,
            dry_run=False,
            format="%Y-%m-%d",
            day_begins=0,
            from_date=None,
            to_date=None,
            yes=True,
        )

        mock_sorter = MagicMock()
        with patch(
            "exif_sorter.sorter.MediaFileSorter", return_value=mock_sorter
        ):
            cmd_sort(args)

        mock_sorter.sort.assert_called_once()

    def test_cmd_sort_dry_run(
        self,
        temp_source_dir: Path,
        temp_dest_dir: Path,
        mock_exiftool_success,
    ):
        """Test sort command with dry run mode."""
        args = argparse.Namespace(
            source=str(temp_source_dir),
            dest=str(temp_dest_dir),
            log_file="test.log",
            copy=False,
            dry_run=True,
            format="%Y-%m-%d",
            day_begins=0,
            from_date=None,
            to_date=None,
            yes=False,
        )

        mock_sorter = MagicMock()
        with patch(
            "exif_sorter.sorter.MediaFileSorter", return_value=mock_sorter
        ):
            cmd_sort(args)

        assert mock_sorter.dry_run is True
        mock_sorter.sort.assert_called_once()

    def test_cmd_sort_with_date_range(
        self,
        temp_source_dir: Path,
        temp_dest_dir: Path,
        mock_exiftool_success,
    ):
        """Test sort command with date range."""
        args = argparse.Namespace(
            source=str(temp_source_dir),
            dest=str(temp_dest_dir),
            log_file="test.log",
            copy=True,
            dry_run=False,
            format="%Y-%m-%d",
            day_begins=0,
            from_date=date(2023, 12, 1),
            to_date=date(2023, 12, 31),
            yes=False,
        )

        mock_sorter = MagicMock()
        with patch(
            "exif_sorter.sorter.MediaFileSorter", return_value=mock_sorter
        ):
            cmd_sort(args)

        assert mock_sorter.from_date == date(2023, 12, 1)
        assert mock_sorter.to_date == date(2023, 12, 31)

    def test_cmd_sort_with_custom_format(
        self,
        temp_source_dir: Path,
        temp_dest_dir: Path,
        mock_exiftool_success,
    ):
        """Test sort command with custom date format."""
        args = argparse.Namespace(
            source=str(temp_source_dir),
            dest=str(temp_dest_dir),
            log_file="test.log",
            copy=True,
            dry_run=False,
            format="%Y/%m/%d",
            day_begins=4,
            from_date=None,
            to_date=None,
            yes=False,
        )

        mock_sorter = MagicMock()
        with patch(
            "exif_sorter.sorter.MediaFileSorter", return_value=mock_sorter
        ):
            cmd_sort(args)

        assert mock_sorter.date_format == "%Y/%m/%d"
        assert mock_sorter.day_begins == 4


class TestCmdClean:
    """Test cmd_clean function."""

    def test_cmd_clean(self, temp_source_dir: Path):
        """Test clean command."""
        args = argparse.Namespace(directory=str(temp_source_dir))

        with patch(
            "exif_sorter.utils.dsstore.remove_ds_store_files"
        ) as mock_remove:
            cmd_clean(args)

        mock_remove.assert_called_once_with(str(temp_source_dir), verbose=True)


class TestCmdDedup:
    """Test cmd_dedup function."""

    def test_cmd_dedup_confirmed(self, temp_source_dir: Path, monkeypatch):
        """Test dedup command with confirmation."""
        monkeypatch.setattr("builtins.input", lambda _: "yes")

        args = argparse.Namespace(
            directory=str(temp_source_dir),
            dry_run=False,
            log_file=None,
            yes=False,
        )

        with patch(
            "exif_sorter.utils.duplicates.remove_duplicates_in_directory",
            return_value=5,
        ) as mock_dedup:
            cmd_dedup(args)

        mock_dedup.assert_called_once_with(
            str(temp_source_dir), dry_run=False, verbose=True
        )

    def test_cmd_dedup_declined(self, temp_source_dir: Path, monkeypatch):
        """Test dedup command when declined."""
        monkeypatch.setattr("builtins.input", lambda _: "no")

        args = argparse.Namespace(
            directory=str(temp_source_dir),
            dry_run=False,
            log_file=None,
            yes=False,
        )

        with (
            patch(
                "exif_sorter.utils.duplicates.remove_duplicates_in_directory"
            ) as mock_dedup,
            pytest.raises(SystemExit),
        ):
            cmd_dedup(args)

        mock_dedup.assert_not_called()

    def test_cmd_dedup_with_yes_flag(self, temp_source_dir: Path):
        """Test dedup command with --yes flag."""
        args = argparse.Namespace(
            directory=str(temp_source_dir),
            dry_run=False,
            log_file="dedup.log",
            yes=True,
        )

        with patch(
            "exif_sorter.utils.duplicates.remove_duplicates_in_directory",
            return_value=3,
        ) as mock_dedup:
            cmd_dedup(args)

        mock_dedup.assert_called_once()

    def test_cmd_dedup_dry_run(self, temp_source_dir: Path):
        """Test dedup command in dry run mode."""
        args = argparse.Namespace(
            directory=str(temp_source_dir),
            dry_run=True,
            log_file=None,
            yes=False,
        )

        with patch(
            "exif_sorter.utils.duplicates.remove_duplicates_in_directory",
            return_value=2,
        ) as mock_dedup:
            cmd_dedup(args)

        mock_dedup.assert_called_once_with(
            str(temp_source_dir), dry_run=True, verbose=True
        )


class TestMainCLI:
    """Test main CLI entry point."""

    def test_main_version(self, capsys):
        """Test --version flag."""
        with (
            patch.object(sys, "argv", ["exif-sorter", "--version"]),
            pytest.raises(SystemExit) as exc_info,
        ):
            main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert __version__ in captured.out

    def test_main_no_command(self):
        """Test running without a command shows error."""
        with (
            patch.object(sys, "argv", ["exif-sorter"]),
            pytest.raises(SystemExit) as exc_info,
        ):
            main()

        assert exc_info.value.code != 0

    def test_main_sort_command(
        self, temp_source_dir: Path, temp_dest_dir: Path, mock_exiftool_success
    ):
        """Test running sort command."""
        with (
            patch.object(
                sys,
                "argv",
                [
                    "exif-sorter",
                    "sort",
                    str(temp_source_dir),
                    str(temp_dest_dir),
                    "--copy",
                    "--dry-run",
                ],
            ),
            patch("exif_sorter.sorter.MediaFileSorter") as mock_sorter_class,
        ):
            mock_sorter = MagicMock()
            mock_sorter_class.return_value = mock_sorter
            main()

        mock_sorter.sort.assert_called_once()

    def test_main_clean_command(self, temp_source_dir: Path):
        """Test running clean command."""
        with (
            patch.object(
                sys, "argv", ["exif-sorter", "clean", str(temp_source_dir)]
            ),
            patch(
                "exif_sorter.utils.dsstore.remove_ds_store_files"
            ) as mock_clean,
        ):
            main()

        mock_clean.assert_called_once()

    def test_main_dedup_command(self, temp_source_dir: Path):
        """Test running dedup command."""
        with (
            patch.object(
                sys,
                "argv",
                ["exif-sorter", "dedup", str(temp_source_dir), "--dry-run"],
            ),
            patch(
                "exif_sorter.utils.duplicates.remove_duplicates_in_directory",
                return_value=0,
            ) as mock_dedup,
        ):
            main()

        mock_dedup.assert_called_once()

    def test_main_sort_with_all_options(
        self, temp_source_dir: Path, temp_dest_dir: Path, mock_exiftool_success
    ):
        """Test sort command with all options."""
        with (
            patch.object(
                sys,
                "argv",
                [
                    "exif-sorter",
                    "sort",
                    str(temp_source_dir),
                    str(temp_dest_dir),
                    "--copy",
                    "--dry-run",
                    "--format",
                    "%Y/%m",
                    "--day-begins",
                    "4",
                    "--from-date",
                    "2023-01-01",
                    "--to-date",
                    "2023-12-31",
                    "--log-file",
                    "custom.log",
                    "--yes",
                ],
            ),
            patch("exif_sorter.sorter.MediaFileSorter") as mock_sorter_class,
        ):
            mock_sorter = MagicMock()
            mock_sorter_class.return_value = mock_sorter
            main()

        mock_sorter_class.assert_called_once()
        assert mock_sorter.date_format == "%Y/%m"
        assert mock_sorter.day_begins == 4
        assert mock_sorter.from_date == date(2023, 1, 1)
        assert mock_sorter.to_date == date(2023, 12, 31)

    def test_main_invalid_date_format(self):
        """Test invalid date format raises error."""
        with (
            patch.object(
                sys,
                "argv",
                [
                    "exif-sorter",
                    "sort",
                    "/source",
                    "/dest",
                    "--from-date",
                    "invalid",
                ],
            ),
            pytest.raises(SystemExit) as exc_info,
        ):
            main()

        assert exc_info.value.code != 0

    def test_main_invalid_day_begins(self):
        """Test invalid day-begins value raises error."""
        with (
            patch.object(
                sys,
                "argv",
                [
                    "exif-sorter",
                    "sort",
                    "/source",
                    "/dest",
                    "--day-begins",
                    "25",  # Out of range 0-23
                ],
            ),
            pytest.raises(SystemExit) as exc_info,
        ):
            main()

        assert exc_info.value.code != 0
