# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

EXIF Sorter - A Python package for organizing photos, videos, and audio files based on EXIF/ID3 metadata creation dates. Designed for managing large media collections (tested with 18,000+ files, ~175GB).

## Prerequisites

- Python 3.11+
- `exiftool` system package (`sudo apt install exiftool`)

## Installation

```bash
pip install -e .
```

## Common Commands

```bash
# Sort media files by date - MOVES files by default
exif-sorter sort <source_dir> <dest_dir>

# Advanced sorting options
exif-sorter sort <src> <dest> --format "%Y/%m"      # Custom folder format
exif-sorter sort <src> <dest> --day-begins 4        # 2am photos → previous day
exif-sorter sort <src> <dest> --from-date 2023-01-01 --to-date 2023-12-31
exif-sorter sort <src> <dest> --copy                # Copy instead of move
exif-sorter sort <src> <dest> --dry-run             # Preview only

# Remove .DS_Store files
exif-sorter clean <directory>

# Remove duplicate files (uses imohash)
exif-sorter dedup <directory> [--dry-run]
```

## Docker Commands

```bash
# Build image locally
docker build -t davidamacey/exif-sorter:latest .

# Run with mounted volumes
docker run --rm -v /input:/input -v /output:/output davidamacey/exif-sorter sort /input /output

# Test the image
docker run --rm davidamacey/exif-sorter --help
```

## Architecture

### Package Structure (`src/exif_sorter/`)

- **cli.py**: CLI entry point with subcommands (`sort`, `clean`, `dedup`)
- **sorter.py**: `MediaFileSorter` class - main sorting logic
- **utils/exif.py**: EXIF date extraction + filename pattern fallback
- **utils/duplicates.py**: `DuplicateFileRemover` class using `imohash`
- **utils/dsstore.py**: Concurrent `.DS_Store` file removal

### Date Extraction Priority (uses LOCAL time, not UTC)

1. `QuickTime:CreationDate` (videos, M4A - has timezone, correct local date)
2. `QuickTime:CreateDate` (videos, M4A - fallback, may be UTC)
3. `EXIF:DateTimeOriginal` / `EXIF:CreateDate` (photos)
4. `ID3:RecordingTime` / `ID3:Year` (MP3 audio)
5. `RIFF:DateTimeOriginal` / `RIFF:DateCreated` (WAV audio)
6. `File:FileModifyDate` (fallback, only option for .AAE files)
7. **Filename patterns** (e.g., `IMG_20231225_143022.jpg`, `VN_20231225.m4a`)

### Key Features

- **Custom folder format**: `--format "%Y/%m/%d"` using strftime patterns
- **Day-begins hour**: `--day-begins 4` for event photography (early AM → previous day)
- **Date range filter**: `--from-date` / `--to-date` to process specific periods
- **Filename fallback**: Extracts dates from `IMG_YYYYMMDD_HHMMSS` patterns
- **Fast hashing**: `imohash` samples ~16KB instead of reading entire file
- **Concurrent processing**: `thread_map` for parallel file operations

### Key Behaviors

- Sorting moves files by default (set `--copy` to keep originals)
- Files without dates go to `00_no_date_found/`
- Files that error go to `00_media_error/`
- Duplicate filenames handled with `_1`, `_2` suffixes
- Log files auto-generated: `sort_YYYY-MM-DD_HHMMSS.log`, `dedup.log`

### Folder Structure

- `src/exif_sorter/` - Main package code
- `Dockerfile` - Docker image definition (Python 3.13 Alpine + exiftool)
- `.github/workflows/ci.yml` - CI/CD pipeline (lint, test, Docker build/push)
- `pyproject.toml` - Package configuration
- `CHANGELOG.md` - Version history

### CI/CD

GitHub Actions workflow:
1. **lint**: Runs ruff on source code
2. **test**: Runs pytest on Python 3.11, 3.12, 3.13
3. **docker**: Builds and pushes multi-arch image (amd64/arm64) to DockerHub

Docker push requires repository secrets:
- `DOCKERHUB_USERNAME`: DockerHub username
- `DOCKERHUB_TOKEN`: DockerHub access token
