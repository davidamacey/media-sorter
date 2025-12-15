"""Tests for duplicate file detection and removal."""

from __future__ import annotations

from pathlib import Path

import pytest

from media_sorter.utils.duplicates import (
    DuplicateFileRemover,
    remove_duplicates_in_directory,
)


class TestDuplicateFileRemover:
    """Test DuplicateFileRemover class."""

    def test_init_default(self):
        """Test initialization with default parameters."""
        remover = DuplicateFileRemover()
        assert remover.dry_run is False
        assert len(remover.file_hashes) == 0

    def test_init_dry_run(self):
        """Test initialization with dry_run enabled."""
        remover = DuplicateFileRemover(dry_run=True)
        assert remover.dry_run is True

    def test_hash_file_consistent(self, temp_source_dir: Path):
        """Test that hashing same file twice returns same hash."""
        file = temp_source_dir / "test.jpg"
        file.write_text("test content for hashing")

        remover = DuplicateFileRemover()
        hash1 = remover.hash_file(str(file))
        hash2 = remover.hash_file(str(file))

        assert hash1 == hash2
        assert isinstance(hash1, str)
        assert len(hash1) > 0

    def test_hash_file_different_content(self, temp_source_dir: Path):
        """Test that different files have different hashes."""
        file1 = temp_source_dir / "file1.jpg"
        file2 = temp_source_dir / "file2.jpg"

        file1.write_text("content 1")
        file2.write_text("content 2")

        remover = DuplicateFileRemover()
        hash1 = remover.hash_file(str(file1))
        hash2 = remover.hash_file(str(file2))

        assert hash1 != hash2

    def test_hash_file_same_content(self, sample_duplicate_files: tuple[Path, Path]):
        """Test that identical files have same hash."""
        file1, file2 = sample_duplicate_files

        remover = DuplicateFileRemover()
        hash1 = remover.hash_file(str(file1))
        hash2 = remover.hash_file(str(file2))

        assert hash1 == hash2

    def test_find_duplicates_no_duplicates(self, temp_source_dir: Path):
        """Test finding duplicates when there are none."""
        file1 = temp_source_dir / "file1.jpg"
        file2 = temp_source_dir / "file2.jpg"

        file1.write_text("content 1")
        file2.write_text("content 2")

        remover = DuplicateFileRemover()
        remover.find_duplicates(str(temp_source_dir))

        # Each file should have unique hash
        assert len(remover.file_hashes) == 2
        for paths in remover.file_hashes.values():
            assert len(paths) == 1

    def test_find_duplicates_with_duplicates(
        self, temp_source_dir: Path, sample_duplicate_files: tuple[Path, Path]
    ):
        """Test finding duplicate files."""
        remover = DuplicateFileRemover()
        remover.find_duplicates(str(temp_source_dir))

        # Should have one hash with two files
        duplicate_groups = [
            paths for paths in remover.file_hashes.values() if len(paths) > 1
        ]
        assert len(duplicate_groups) == 1
        assert len(duplicate_groups[0]) == 2

    def test_find_duplicates_ignores_hidden_files(self, temp_source_dir: Path):
        """Test that hidden files are ignored."""
        visible = temp_source_dir / "visible.jpg"
        hidden = temp_source_dir / ".hidden.jpg"

        visible.write_text("content")
        hidden.write_text("content")

        remover = DuplicateFileRemover()
        remover.find_duplicates(str(temp_source_dir))

        # Only visible file should be found
        assert len(remover.file_hashes) == 1
        for paths in remover.file_hashes.values():
            assert ".hidden" not in paths[0]

    def test_remove_file_dry_run(self, temp_source_dir: Path, capsys):
        """Test removing file in dry run mode."""
        file = temp_source_dir / "test.jpg"
        file.write_text("content")

        remover = DuplicateFileRemover(dry_run=True)
        remover.remove_file(str(file))

        # File should still exist
        assert file.exists()

        # Should have printed message
        captured = capsys.readouterr()
        assert "Would remove" in captured.out

    def test_remove_file_actual(self, temp_source_dir: Path):
        """Test actually removing file."""
        file = temp_source_dir / "test.jpg"
        file.write_text("content")

        remover = DuplicateFileRemover(dry_run=False)
        remover.remove_file(str(file))

        # File should be removed
        assert not file.exists()

    def test_remove_duplicates_keeps_shortest_name(
        self, sample_duplicate_files: tuple[Path, Path]
    ):
        """Test that duplicate removal keeps file with shortest name."""
        file1, file2 = sample_duplicate_files

        remover = DuplicateFileRemover(dry_run=False)
        remover.find_duplicates(str(file1.parent))
        remover.remove_duplicates()

        # Shorter filename should be kept
        assert file1.exists()
        assert not file2.exists()

    def test_remove_duplicates_dry_run(
        self, sample_duplicate_files: tuple[Path, Path]
    ):
        """Test removing duplicates in dry run mode."""
        file1, file2 = sample_duplicate_files

        remover = DuplicateFileRemover(dry_run=True)
        remover.find_duplicates(str(file1.parent))
        remover.remove_duplicates()

        # Both files should still exist
        assert file1.exists()
        assert file2.exists()

    def test_remove_duplicates_multiple_groups(self, temp_source_dir: Path):
        """Test removing duplicates with multiple duplicate groups."""
        # First group of duplicates
        dup1a = temp_source_dir / "dup1_short.jpg"
        dup1b = temp_source_dir / "dup1_longer_name.jpg"
        dup1a.write_text("content group 1")
        dup1b.write_text("content group 1")

        # Second group of duplicates
        dup2a = temp_source_dir / "dup2_x.jpg"
        dup2b = temp_source_dir / "dup2_y_longer.jpg"
        dup2a.write_text("content group 2")
        dup2b.write_text("content group 2")

        # Unique file
        unique = temp_source_dir / "unique.jpg"
        unique.write_text("unique content")

        remover = DuplicateFileRemover(dry_run=False)
        remover.find_duplicates(str(temp_source_dir))
        remover.remove_duplicates()

        # Shorter names should be kept
        assert dup1a.exists()
        assert not dup1b.exists()
        assert dup2a.exists()
        assert not dup2b.exists()
        assert unique.exists()

    def test_remove_duplicates_three_copies(self, temp_source_dir: Path):
        """Test removing when there are three copies of same file."""
        file1 = temp_source_dir / "a.jpg"
        file2 = temp_source_dir / "bb.jpg"
        file3 = temp_source_dir / "ccc.jpg"

        content = "identical content"
        file1.write_text(content)
        file2.write_text(content)
        file3.write_text(content)

        remover = DuplicateFileRemover(dry_run=False)
        remover.find_duplicates(str(temp_source_dir))
        remover.remove_duplicates()

        # Only shortest should remain
        assert file1.exists()
        assert not file2.exists()
        assert not file3.exists()

    def test_get_removed_count_no_duplicates(self, temp_source_dir: Path):
        """Test get_removed_count when there are no duplicates."""
        file1 = temp_source_dir / "file1.jpg"
        file2 = temp_source_dir / "file2.jpg"

        file1.write_text("content 1")
        file2.write_text("content 2")

        remover = DuplicateFileRemover()
        remover.find_duplicates(str(temp_source_dir))

        assert remover.get_removed_count() == 0

    def test_get_removed_count_with_duplicates(
        self, sample_duplicate_files: tuple[Path, Path]
    ):
        """Test get_removed_count with duplicates."""
        remover = DuplicateFileRemover()
        remover.find_duplicates(str(sample_duplicate_files[0].parent))

        # 2 files with same hash = 1 removal
        assert remover.get_removed_count() == 1

    def test_get_removed_count_multiple_groups(self, temp_source_dir: Path):
        """Test get_removed_count with multiple duplicate groups."""
        # Group 1: 3 duplicates
        for i in range(3):
            file = temp_source_dir / f"group1_{i}.jpg"
            file.write_text("group 1 content")

        # Group 2: 2 duplicates
        for i in range(2):
            file = temp_source_dir / f"group2_{i}.jpg"
            file.write_text("group 2 content")

        # Unique file
        (temp_source_dir / "unique.jpg").write_text("unique")

        remover = DuplicateFileRemover()
        remover.find_duplicates(str(temp_source_dir))

        # Group 1: 3 files = 2 removals
        # Group 2: 2 files = 1 removal
        # Total: 3 removals
        assert remover.get_removed_count() == 3


class TestRemoveDuplicatesInDirectory:
    """Test remove_duplicates_in_directory function."""

    def test_remove_duplicates_single_subdir(self, temp_source_dir: Path):
        """Test removing duplicates in single subdirectory."""
        subdir = temp_source_dir / "2023-12-25"
        subdir.mkdir()

        file1 = subdir / "short.jpg"
        file2 = subdir / "longer_name.jpg"
        file1.write_text("duplicate content")
        file2.write_text("duplicate content")

        total = remove_duplicates_in_directory(
            str(temp_source_dir), dry_run=False, verbose=False
        )

        assert total == 1
        assert file1.exists()
        assert not file2.exists()

    def test_remove_duplicates_multiple_subdirs(self, temp_source_dir: Path):
        """Test removing duplicates in multiple subdirectories."""
        subdir1 = temp_source_dir / "2023-12-25"
        subdir2 = temp_source_dir / "2023-12-26"
        subdir1.mkdir()
        subdir2.mkdir()

        # Duplicates in first subdir
        file1a = subdir1 / "a.jpg"
        file1b = subdir1 / "bb.jpg"
        file1a.write_text("content 1")
        file1b.write_text("content 1")

        # Duplicates in second subdir
        file2a = subdir2 / "x.jpg"
        file2b = subdir2 / "yy.jpg"
        file2a.write_text("content 2")
        file2b.write_text("content 2")

        total = remove_duplicates_in_directory(
            str(temp_source_dir), dry_run=False, verbose=False
        )

        assert total == 2
        assert file1a.exists() and not file1b.exists()
        assert file2a.exists() and not file2b.exists()

    def test_remove_duplicates_dry_run(self, temp_source_dir: Path):
        """Test dry run mode doesn't delete files."""
        subdir = temp_source_dir / "2023-12-25"
        subdir.mkdir()

        file1 = subdir / "short.jpg"
        file2 = subdir / "longer_name.jpg"
        file1.write_text("duplicate content")
        file2.write_text("duplicate content")

        total = remove_duplicates_in_directory(
            str(temp_source_dir), dry_run=True, verbose=False
        )

        assert total == 1
        # Both files should still exist
        assert file1.exists()
        assert file2.exists()

    def test_remove_duplicates_no_subdirs(self, temp_source_dir: Path):
        """Test when there are no subdirectories."""
        # Create files directly in temp_source_dir
        file1 = temp_source_dir / "file1.jpg"
        file1.write_text("content")

        total = remove_duplicates_in_directory(
            str(temp_source_dir), dry_run=False, verbose=False
        )

        assert total == 0

    def test_remove_duplicates_empty_subdirs(self, temp_source_dir: Path):
        """Test with empty subdirectories."""
        subdir1 = temp_source_dir / "empty1"
        subdir2 = temp_source_dir / "empty2"
        subdir1.mkdir()
        subdir2.mkdir()

        total = remove_duplicates_in_directory(
            str(temp_source_dir), dry_run=False, verbose=False
        )

        assert total == 0

    def test_remove_duplicates_preserves_across_subdirs(self, temp_source_dir: Path):
        """Test that duplicates are only removed within subdirectories, not across them."""
        subdir1 = temp_source_dir / "2023-12-25"
        subdir2 = temp_source_dir / "2023-12-26"
        subdir1.mkdir()
        subdir2.mkdir()

        # Same content in different subdirectories
        file1 = subdir1 / "photo.jpg"
        file2 = subdir2 / "photo.jpg"
        file1.write_text("same content")
        file2.write_text("same content")

        total = remove_duplicates_in_directory(
            str(temp_source_dir), dry_run=False, verbose=False
        )

        # Files should not be considered duplicates across subdirs
        assert total == 0
        assert file1.exists()
        assert file2.exists()

    def test_remove_duplicates_ignores_files_in_root(self, temp_source_dir: Path):
        """Test that files in root directory are ignored."""
        # Files in root
        root_file1 = temp_source_dir / "root1.jpg"
        root_file2 = temp_source_dir / "root2.jpg"
        root_file1.write_text("duplicate")
        root_file2.write_text("duplicate")

        # Subdirectory with different files
        subdir = temp_source_dir / "2023-12-25"
        subdir.mkdir()
        subdir_file = subdir / "photo.jpg"
        subdir_file.write_text("unique")

        total = remove_duplicates_in_directory(
            str(temp_source_dir), dry_run=False, verbose=False
        )

        # Root duplicates should not be processed
        assert total == 0
        assert root_file1.exists()
        assert root_file2.exists()

    def test_remove_duplicates_verbose_output(self, temp_source_dir: Path, capsys):
        """Test verbose output."""
        subdir = temp_source_dir / "2023-12-25"
        subdir.mkdir()

        file1 = subdir / "a.jpg"
        file2 = subdir / "b.jpg"
        file1.write_text("duplicate")
        file2.write_text("duplicate")

        remove_duplicates_in_directory(
            str(temp_source_dir), dry_run=False, verbose=True
        )

        captured = capsys.readouterr()
        assert "Processing directories" in captured.out or captured.err

    def test_remove_duplicates_nested_subdirs(self, temp_source_dir: Path):
        """Test that nested subdirectories are processed independently."""
        # Create nested structure: parent/child
        parent = temp_source_dir / "parent"
        child = parent / "child"
        parent.mkdir()
        child.mkdir()

        # Duplicates in parent
        p1 = parent / "a.jpg"
        p2 = parent / "bb.jpg"
        p1.write_text("parent content")
        p2.write_text("parent content")

        # Duplicates in child
        c1 = child / "x.jpg"
        c2 = child / "yy.jpg"
        c1.write_text("child content")
        c2.write_text("child content")

        # This will process top-level subdirectories (parent and any siblings)
        total = remove_duplicates_in_directory(
            str(temp_source_dir), dry_run=False, verbose=False
        )

        # Should find duplicates in parent directory
        assert total >= 1
