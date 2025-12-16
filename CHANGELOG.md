# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-12-15

### Added

- **Docker support**: Official Docker image for portable, zero-install usage
  - Available at `davidamacey/exif-sorter` on Docker Hub
  - Multi-architecture support (amd64, arm64)
  - Based on Python 3.13 Alpine for minimal image size (~116MB)
- **CI/CD pipeline**: Automated Docker image builds and publishing
  - Builds on every push to main after tests pass
  - Automatic version tagging from pyproject.toml

### Changed

- README restructured with Docker as primary quick-start option
- Added Acknowledgments section crediting ExifTool

### Fixed

- CLI now correctly shows `exif-sorter` instead of legacy `media-sorter` in help/version

## [1.0.1] - 2025-12-14

### Fixed

- **Dry-run mode**: No longer creates `00_no_date_found` and `00_media_error` folders when using `--dry-run`
- **Log file naming**: Changed default log filename from `sort_YYYY-MM-DD.log` to `sort_YYYY-MM-DD_HHMMSS.log` to prevent overwrites on multiple runs

## [1.0.0] - 2025-12-14

### Added

- **CLI with subcommands**: `sort`, `clean`, and `dedup`
- **Multi-format support**: Photos (JPEG, PNG, HEIC, RAW), videos (MP4, MOV, M4V), and audio (MP3, WAV, M4A)
- **EXIF-based sorting**: Organize media into date-based folders using metadata
- **Audio metadata support**: ID3 tags for MP3, RIFF tags for WAV, QuickTime for M4A
- **Filename date fallback**: Extract dates from filenames like `IMG_20231225_143022.jpg`, `VN_20231225.m4a`
- **Custom folder formats**: Configure date folder structure with `--format` (strftime)
- **Day boundary option**: `--day-begins` to handle late-night photos (e.g., 2am → previous day)
- **Date range filtering**: `--from-date` and `--to-date` to process specific periods
- **Duplicate detection**: Fast file comparison using [imohash](https://pypi.org/project/imohash/)
- **Dry run mode**: Preview changes with `--dry-run` before executing
- **Copy mode**: Use `--copy` to keep source files instead of moving
- **Confirmation prompts**: Destructive operations require confirmation (skip with `--yes`)
- **Thread-safe processing**: Concurrent file operations with proper locking
- **DS_Store cleanup**: Automatic removal during sort, or standalone `clean` command
- **Empty folder cleanup**: Remove empty source directories after sorting
- **Comprehensive logging**: Track processed files and errors

### Technical

- Python 3.11+ required
- Full type annotations throughout codebase
- Ruff linting and formatting (PEP 8 compliant)
- Input validation for source/destination directories
- exiftool dependency check on startup

### Dependencies

- PyExifTool (EXIF/QuickTime metadata extraction)
- imohash (fast file hashing via sampling)
- tqdm (progress bars and concurrent processing)

[1.1.0]: https://github.com/davidamacey/exif-sorter/releases/tag/v1.1.0
[1.0.1]: https://github.com/davidamacey/exif-sorter/releases/tag/v1.0.1
[1.0.0]: https://github.com/davidamacey/exif-sorter/releases/tag/v1.0.0
