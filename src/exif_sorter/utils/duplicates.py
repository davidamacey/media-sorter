"""Utility for finding and removing duplicate files using imohash."""

from __future__ import annotations

import logging
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from os import listdir, path, remove, walk

from imohash import hashfile
from tqdm import tqdm


class DuplicateFileRemover:
    """Find and remove duplicate files based on imohash (fast sampling hash)."""

    file_hashes: defaultdict[str, list[str]]
    dry_run: bool

    def __init__(self, dry_run: bool = False) -> None:
        self.file_hashes = defaultdict(list)
        self.dry_run = dry_run

    def hash_file(self, file_path: str) -> str:
        """Calculate the imohash of a file (fast, samples file content)."""
        result: str = hashfile(file_path, hexdigest=True)
        return result

    def _hash_and_store(self, file_path: str) -> None:
        """Hash a file and store it in the dictionary."""
        try:
            file_hash = self.hash_file(file_path)
            self.file_hashes[file_hash].append(file_path)
        except Exception as e:
            logging.error(f"Error hashing {file_path}: {e}")

    def remove_file(self, filepath: str) -> None:
        """Remove a file and log the action."""
        if self.dry_run:
            logging.info(f"Would remove duplicate: {filepath}")
            print(f"Would remove: {filepath}")
        else:
            try:
                remove(filepath)
                logging.info(f"Removed duplicate: {filepath}")
            except Exception as e:
                logging.error(f"Error removing {filepath}: {e}")

    def find_duplicates(self, directory: str) -> None:
        """Find duplicate files in the specified directory."""
        file_paths: list[str] = [
            path.join(root, file)
            for root, _, files in walk(directory)
            for file in files
            if not file.startswith(".")
        ]
        with ThreadPoolExecutor() as executor:
            list(executor.map(self._hash_and_store, file_paths))

    def remove_duplicates(self) -> None:
        """Remove duplicate files, keeping the shortest filenames."""
        duplicates: dict[str, list[str]] = {
            file_hash: paths
            for file_hash, paths in self.file_hashes.items()
            if len(paths) > 1
        }
        for paths in duplicates.values():
            paths.sort(key=len)
            for filepath in paths[1:]:
                self.remove_file(filepath)

    def get_removed_count(self) -> int:
        """Get the count of files that were/would be removed."""
        return sum(
            len(paths) - 1
            for paths in self.file_hashes.values()
            if len(paths) > 1
        )


def remove_duplicates_in_directory(
    directory: str, dry_run: bool = False, verbose: bool = True
) -> int:
    """Process all subdirectories within a directory for duplicates.

    Args:
        directory: Root directory to process
        dry_run: If True, only report what would be removed
        verbose: Print progress

    Returns:
        Total count of removed (or would-be-removed) files
    """
    subdirectories: list[str] = [
        path.join(directory, d)
        for d in listdir(directory)
        if path.isdir(path.join(directory, d))
    ]

    total_removed = 0
    pbar = tqdm(
        total=len(subdirectories),
        disable=not verbose,
        desc="Processing directories",
    )

    for subdir in subdirectories:
        remover = DuplicateFileRemover(dry_run=dry_run)
        remover.find_duplicates(subdir)
        remover.remove_duplicates()

        removed = remover.get_removed_count()
        total_removed += removed
        logging.info(f"Files removed in {subdir}: {removed}")

        pbar.update(1)

    pbar.close()
    logging.info(f"Finished checking for duplicate files in: {directory}")

    return total_removed
