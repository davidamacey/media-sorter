"""Shared pytest fixtures for exif-sorter tests."""

from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def temp_source_dir(tmp_path: Path) -> Path:
    """Create a temporary source directory."""
    source = tmp_path / "source"
    source.mkdir()
    return source


@pytest.fixture
def temp_dest_dir(tmp_path: Path) -> Path:
    """Create a temporary destination directory."""
    dest = tmp_path / "dest"
    dest.mkdir()
    return dest


@pytest.fixture
def sample_image_file(temp_source_dir: Path) -> Path:
    """Create a sample image file with a date in filename."""
    img_file = temp_source_dir / "IMG_20231225_143022.jpg"
    img_file.write_text("fake image data")
    return img_file


@pytest.fixture
def sample_video_file(temp_source_dir: Path) -> Path:
    """Create a sample video file with a date in filename."""
    vid_file = temp_source_dir / "VID_20231225_153045.mp4"
    vid_file.write_text("fake video data")
    return vid_file


@pytest.fixture
def sample_audio_file(temp_source_dir: Path) -> Path:
    """Create a sample audio file with a date in filename."""
    aud_file = temp_source_dir / "VN_20231225_143022.m4a"
    aud_file.write_text("fake audio data")
    return aud_file


@pytest.fixture
def sample_file_no_date(temp_source_dir: Path) -> Path:
    """Create a sample file with no date in filename."""
    file = temp_source_dir / "random_photo.jpg"
    file.write_text("fake image data")
    return file


@pytest.fixture
def sample_files_with_dates(temp_source_dir: Path) -> list[Path]:
    """Create multiple sample files with various date patterns."""
    files = [
        "IMG_20231225_143022.jpg",
        "VID_20231226_120000.mp4",
        "2023-12-27_photo.jpg",
        "20231228.png",
        "VN_20231229_090000.m4a",
    ]

    created_files = []
    for filename in files:
        file_path = temp_source_dir / filename
        file_path.write_text(f"fake data for {filename}")
        created_files.append(file_path)

    return created_files


@pytest.fixture
def mock_exiftool_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock successful exiftool execution."""
    def mock_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess:
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout="12.50",
            stderr=""
        )

    monkeypatch.setattr(subprocess, "run", mock_run)


@pytest.fixture
def mock_exiftool_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock exiftool not found."""
    def mock_run(*args: Any, **kwargs: Any) -> None:
        raise FileNotFoundError("exiftool not found")

    monkeypatch.setattr(subprocess, "run", mock_run)


@pytest.fixture
def mock_exiftool_metadata(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Mock ExifToolHelper to return sample metadata."""
    metadata = {
        "EXIF:DateTimeOriginal": "2023:12:25 14:30:22",
        "File:FileType": "JPEG",
    }

    class MockExifToolHelper:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def get_metadata(self, file_path: str) -> list[dict[str, Any]]:
            return [metadata]

    import exif_sorter.utils.exif
    monkeypatch.setattr(
        exif_sorter.utils.exif, "ExifToolHelper", MockExifToolHelper
    )

    return metadata


@pytest.fixture
def mock_exiftool_no_date(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock ExifToolHelper to return metadata without date."""
    class MockExifToolHelper:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def get_metadata(self, file_path: str) -> list[dict[str, Any]]:
            return [{"File:FileType": "JPEG"}]

    import exif_sorter.utils.exif
    monkeypatch.setattr(
        exif_sorter.utils.exif, "ExifToolHelper", MockExifToolHelper
    )


@pytest.fixture
def mock_exiftool_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock ExifToolHelper to raise an error."""
    class MockExifToolHelper:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def get_metadata(self, file_path: str) -> list[dict[str, Any]]:
            raise RuntimeError("ExifTool error")

    import exif_sorter.utils.exif
    monkeypatch.setattr(
        exif_sorter.utils.exif, "ExifToolHelper", MockExifToolHelper
    )


@pytest.fixture
def sample_duplicate_files(temp_source_dir: Path) -> tuple[Path, Path]:
    """Create two files with identical content."""
    content = "identical content for duplicate test"

    file1 = temp_source_dir / "duplicate1.jpg"
    file2 = temp_source_dir / "duplicate2_with_longer_name.jpg"

    file1.write_text(content)
    file2.write_text(content)

    return file1, file2
