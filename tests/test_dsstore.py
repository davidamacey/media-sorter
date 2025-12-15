"""Tests for DS_Store file removal utilities."""

from __future__ import annotations

from pathlib import Path

import pytest

from media_sorter.utils.dsstore import (
    find_ds_store_files,
    remove_ds_store_file,
    remove_ds_store_files,
)


class TestFindDSStoreFiles:
    """Test find_ds_store_files function."""

    def test_find_single_ds_store(self, temp_source_dir: Path):
        """Test finding a single .DS_Store file."""
        ds_store = temp_source_dir / ".DS_Store"
        ds_store.write_text("ds_store content")

        files = find_ds_store_files(str(temp_source_dir))
        assert len(files) == 1
        assert files[0] == str(ds_store)

    def test_find_multiple_ds_store(self, temp_source_dir: Path):
        """Test finding multiple .DS_Store files."""
        ds_store1 = temp_source_dir / ".DS_Store"
        ds_store2 = temp_source_dir / "subdir" / ".DS_Store"
        ds_store3 = temp_source_dir / "subdir" / "nested" / ".DS_Store"

        ds_store1.write_text("content")
        ds_store2.parent.mkdir()
        ds_store2.write_text("content")
        ds_store3.parent.mkdir(parents=True)
        ds_store3.write_text("content")

        files = find_ds_store_files(str(temp_source_dir))
        assert len(files) == 3
        assert str(ds_store1) in files
        assert str(ds_store2) in files
        assert str(ds_store3) in files

    def test_find_appledouble_ds_store(self, temp_source_dir: Path):
        """Test finding ._.DS_Store (AppleDouble) files."""
        ds_store = temp_source_dir / "._.DS_Store"
        ds_store.write_text("content")

        files = find_ds_store_files(str(temp_source_dir))
        assert len(files) == 1
        assert files[0] == str(ds_store)

    def test_find_both_types(self, temp_source_dir: Path):
        """Test finding both .DS_Store and ._.DS_Store files."""
        ds_store1 = temp_source_dir / ".DS_Store"
        ds_store2 = temp_source_dir / "._.DS_Store"
        ds_store1.write_text("content")
        ds_store2.write_text("content")

        files = find_ds_store_files(str(temp_source_dir))
        assert len(files) == 2

    def test_find_no_ds_store(self, temp_source_dir: Path):
        """Test finding no .DS_Store files."""
        # Create some regular files
        (temp_source_dir / "photo.jpg").write_text("content")
        (temp_source_dir / "video.mp4").write_text("content")

        files = find_ds_store_files(str(temp_source_dir))
        assert len(files) == 0

    def test_find_ignores_similar_names(self, temp_source_dir: Path):
        """Test that files with similar names are ignored."""
        (temp_source_dir / "DS_Store.txt").write_text("content")
        (temp_source_dir / ".DS_Store_backup").write_text("content")
        (temp_source_dir / "my.DS_Store").write_text("content")

        files = find_ds_store_files(str(temp_source_dir))
        assert len(files) == 0

    def test_find_directory_not_exists(self):
        """Test error when directory doesn't exist."""
        with pytest.raises(FileNotFoundError, match="does not exist"):
            find_ds_store_files("/nonexistent/directory")

    def test_find_empty_directory(self, temp_source_dir: Path):
        """Test finding in empty directory."""
        files = find_ds_store_files(str(temp_source_dir))
        assert len(files) == 0


class TestRemoveDSStoreFile:
    """Test remove_ds_store_file function."""

    def test_remove_existing_file(self, temp_source_dir: Path):
        """Test removing an existing .DS_Store file."""
        ds_store = temp_source_dir / ".DS_Store"
        ds_store.write_text("content")

        result = remove_ds_store_file(str(ds_store))
        assert "Removed" in result
        assert not ds_store.exists()

    def test_remove_nonexistent_file(self, temp_source_dir: Path):
        """Test error when trying to remove nonexistent file."""
        ds_store = temp_source_dir / ".DS_Store"

        result = remove_ds_store_file(str(ds_store))
        assert "Error removing" in result


class TestRemoveDSStoreFiles:
    """Test remove_ds_store_files function."""

    def test_remove_single_file_verbose(self, temp_source_dir: Path, capsys):
        """Test removing single file with verbose output."""
        ds_store = temp_source_dir / ".DS_Store"
        ds_store.write_text("content")

        results = remove_ds_store_files(str(temp_source_dir), verbose=True)

        assert len(results) == 1
        assert "Removed" in results[0]
        assert not ds_store.exists()

        captured = capsys.readouterr()
        assert "Removing 1 .DS_Store files" in captured.out

    def test_remove_multiple_files(self, temp_source_dir: Path):
        """Test removing multiple .DS_Store files."""
        ds_store1 = temp_source_dir / ".DS_Store"
        ds_store2 = temp_source_dir / "subdir" / ".DS_Store"
        ds_store3 = temp_source_dir / "._.DS_Store"

        ds_store1.write_text("content")
        ds_store2.parent.mkdir()
        ds_store2.write_text("content")
        ds_store3.write_text("content")

        results = remove_ds_store_files(str(temp_source_dir), verbose=False)

        assert len(results) == 3
        assert not ds_store1.exists()
        assert not ds_store2.exists()
        assert not ds_store3.exists()

    def test_remove_no_files(self, temp_source_dir: Path, capsys):
        """Test when there are no .DS_Store files to remove."""
        results = remove_ds_store_files(str(temp_source_dir), verbose=True)

        assert len(results) == 0
        captured = capsys.readouterr()
        assert "Removing 0 .DS_Store files" in captured.out

    def test_remove_quiet_mode(self, temp_source_dir: Path, capsys):
        """Test removing files without verbose output."""
        ds_store = temp_source_dir / ".DS_Store"
        ds_store.write_text("content")

        results = remove_ds_store_files(str(temp_source_dir), verbose=False)

        assert len(results) == 1
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_remove_preserves_other_files(self, temp_source_dir: Path):
        """Test that only .DS_Store files are removed."""
        ds_store = temp_source_dir / ".DS_Store"
        photo = temp_source_dir / "photo.jpg"
        video = temp_source_dir / "video.mp4"

        ds_store.write_text("ds_store")
        photo.write_text("photo")
        video.write_text("video")

        remove_ds_store_files(str(temp_source_dir), verbose=False)

        assert not ds_store.exists()
        assert photo.exists()
        assert video.exists()

    def test_remove_nested_directories(self, temp_source_dir: Path):
        """Test removing .DS_Store files from nested directories."""
        ds1 = temp_source_dir / ".DS_Store"
        ds2 = temp_source_dir / "a" / ".DS_Store"
        ds3 = temp_source_dir / "a" / "b" / ".DS_Store"
        ds4 = temp_source_dir / "a" / "b" / "c" / ".DS_Store"

        ds1.write_text("content")
        ds2.parent.mkdir()
        ds2.write_text("content")
        ds3.parent.mkdir()
        ds3.write_text("content")
        ds4.parent.mkdir()
        ds4.write_text("content")

        results = remove_ds_store_files(str(temp_source_dir), verbose=False)

        assert len(results) == 4
        assert not ds1.exists()
        assert not ds2.exists()
        assert not ds3.exists()
        assert not ds4.exists()

    def test_remove_with_permission_error(self, temp_source_dir: Path, monkeypatch):
        """Test handling permission errors when removing files."""
        ds_store = temp_source_dir / ".DS_Store"
        ds_store.write_text("content")

        def mock_remove(path):
            if ".DS_Store" in str(path):
                raise PermissionError("Permission denied")

        import media_sorter.utils.dsstore
        monkeypatch.setattr(media_sorter.utils.dsstore, "remove", mock_remove)

        results = remove_ds_store_files(str(temp_source_dir), verbose=False)

        assert len(results) == 1
        assert "Error removing" in results[0]
