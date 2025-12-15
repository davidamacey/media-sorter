"""Utility for removing .DS_Store files from directories."""

from __future__ import annotations

import concurrent.futures
from os import path, remove, walk


def remove_ds_store_file(file_path: str) -> str:
    """Remove a single .DS_Store file."""
    try:
        remove(file_path)
        return f"Removed '{file_path}'"
    except Exception as e:
        return f"Error removing '{file_path}': {e!s}"


def find_ds_store_files(directory: str) -> list[str]:
    """Find all .DS_Store files in a directory tree."""
    if not path.exists(directory):
        raise FileNotFoundError(f"Directory '{directory}' does not exist.")

    return [
        path.join(root, filename)
        for root, _, files in walk(directory)
        for filename in files
        if filename in (".DS_Store", "._.DS_Store")
    ]


def remove_ds_store_files(directory: str, verbose: bool = True) -> list[str]:
    """Remove all .DS_Store files from a directory tree.

    Args:
        directory: Path to directory to clean
        verbose: Print progress messages

    Returns:
        List of result messages
    """
    ds_store_files = find_ds_store_files(directory)

    if verbose:
        print(f"Removing {len(ds_store_files)} .DS_Store files")

    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(executor.map(remove_ds_store_file, ds_store_files))

    if verbose:
        for result in results:
            print(result)

    return results
