# EXIF Sorter

[![PyPI version](https://badge.fury.io/py/exif-sorter.svg)](https://badge.fury.io/py/exif-sorter)
[![Python Version](https://img.shields.io/pypi/pyversions/exif-sorter.svg)](https://pypi.org/project/exif-sorter/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Organize photos, videos, and audio recordings into date-based folders using EXIF/QuickTime/ID3 metadata. Designed for managing large media collections efficiently using concurrent processing.

**Performance:** Using 24 cores with a local NAS, 18,000 files (~175 GB) processed in about 8 minutes.

## Why This Package?

I created this out of my own need to organize media from GoPros, Canon cameras, and iPhones into a `YYYY-MM-DD` folder structure—the same format used by legacy photo organization apps from Canon and others. This structure allows for quick storage by day and handles multiple files and naming conventions cleanly.

When I couldn't find an existing package that did this well, I built my own. It started as a macOS Automator macro and evolved into this pip package as requirements grew: better video support, audio recordings, configurable date formats, day-start boundaries for event photography, and date range filtering.

**Philosophy:** This package is intentionally lean. It serves one function—sorting media by date—and does it well and quickly. No feature creep.

## Installation

### Prerequisites

- Python 3.11+
- `exiftool` system package

```bash
# Install exiftool (Ubuntu/Debian)
sudo apt install exiftool

# Install exiftool (macOS)
brew install exiftool

# Install exiftool (Windows via Chocolatey)
choco install exiftool

# Or via Scoop
scoop install exiftool
```

### Install Package

```bash
# Install from PyPI
pip install exif-sorter

# Or clone and install in development mode
git clone https://github.com/davidamacey/exif-sorter.git
cd exif-sorter
pip install -e .
```

## Usage

After installation, the `exif-sorter` command is available with three subcommands:

### Sort Media Files

Organize media into date-based folders by reading EXIF metadata:

```bash
# Basic usage - sort and MOVE files (default)
exif-sorter sort /path/to/unsorted/ /path/to/sorted/

# Copy instead of move (keeps originals)
exif-sorter sort /path/to/unsorted/ /path/to/sorted/ --copy

# Dry run - preview without changes
exif-sorter sort /path/to/unsorted/ /path/to/sorted/ --dry-run
```

**Advanced options:**

```bash
# Custom folder format (default: %Y-%m-%d)
exif-sorter sort /source/ /dest/ --format "%Y/%m"        # 2023/12/
exif-sorter sort /source/ /dest/ --format "%Y/%B"        # 2023/December/
exif-sorter sort /source/ /dest/ --format "%Y-%m-%d"     # 2023-12-25 (default)

# Day begins at 4am (2am photos go to previous day - useful for events)
exif-sorter sort /source/ /dest/ --day-begins 4

# Filter by date range
exif-sorter sort /source/ /dest/ --from-date 2023-01-01 --to-date 2023-12-31
```

**Default behavior:**
- Moves files (removes from source after successful transfer)
- Creates `00_no_date_found/` for files without date metadata
- Creates `00_media_error/` for files that fail processing
- Falls back to filename date patterns (e.g., `IMG_20231225_143022.jpg`)
- Auto-generates log file: `sort_YYYY-MM-DD.log`
- Removes empty source folders after sorting

### Remove Duplicate Files

Find and remove duplicates within each subdirectory using fast `imohash`:

```bash
# Remove duplicates (keeps file with shortest name)
exif-sorter dedup /path/to/sorted/

# Dry run - see what would be removed
exif-sorter dedup /path/to/sorted/ --dry-run
```

### Clean .DS_Store Files

Remove macOS `.DS_Store` files from a directory tree:

```bash
exif-sorter clean /path/to/directory/
```

## Workflow

Typical workflow for importing photos from iPhone or camera:

```bash
# 1. Sort imported media by date
exif-sorter sort ~/import/ ~/Pictures/

# 2. Clean up macOS artifacts
exif-sorter clean ~/Pictures/

# 3. Remove any duplicates within date folders
exif-sorter dedup ~/Pictures/
```

## iPhone Import Instructions

### Connect iPhone to Linux

1. Connect iPhone via USB
2. Turn off WiFi and Bluetooth, turn on Personal Hotspot
3. In Files app, navigate to Network section
4. Remove the `:3/` from the address to connect to iPhone system

### Copy Files

1. Navigate to iPhone DCIM folder
2. Select folders to copy
3. Drag and drop to your import folder (e.g., `~/import/`)
4. Run the sort workflow above

## Date Extraction Priority

The sorter checks these metadata sources in order:

| Priority | File Types | Metadata Tag | Notes |
|----------|------------|--------------|-------|
| 1 | Videos (MP4, MOV, M4V) | `QuickTime:CreationDate` | Has timezone - correct local date |
| 2 | Videos (MP4, MOV, M4V) | `QuickTime:CreateDate` | Fallback, may be UTC |
| 3 | Photos (JPEG, PNG, HEIC, RAW) | `EXIF:DateTimeOriginal` | |
| 4 | Photos (JPEG, PNG, HEIC, RAW) | `EXIF:CreateDate` | |
| 5 | Audio (MP3) | `ID3:RecordingTime` | ID3v2.4 TDRC tag |
| 6 | Audio (MP3) | `ID3:Year` | Year only |
| 7 | Audio (WAV) | `RIFF:DateTimeOriginal` | IDIT chunk |
| 8 | Audio (WAV) | `RIFF:DateCreated` | ICRD chunk |
| 9 | All files | `File:FileModifyDate` | Universal fallback |
| 10 | All files | Filename patterns | e.g., `IMG_20231225_143022.jpg` |

**Notes:**
- Audio (M4A, AAC) uses QuickTime tags (same as videos)
- `.AAE` sidecar files only use `File:FileModifyDate`

## Duplicate Detection

Duplicates are detected using [imohash](https://pypi.org/project/imohash/), a fast hashing algorithm optimized for large files. Instead of reading entire files, imohash samples ~16KB from the beginning, middle, and end of files along with the file size.

**Benefits:**
- Extremely fast for large media files (videos, RAW photos)
- Suitable for detecting true duplicates (same file copied multiple times)

**Limitations:**
- May produce false positives for files that differ only in the middle sections (rare for media)
- Not suitable for detecting near-duplicates or edited versions of the same photo
- Files must be exactly the same size and have identical sampled sections to match

For most photo/video organization workflows where duplicates are exact copies, imohash provides an excellent speed/accuracy tradeoff.

## Project Structure

```
exif-sorter/
├── src/exif_sorter/      # Main package
│   ├── cli.py            # CLI entry point
│   ├── sorter.py         # MediaFileSorter class
│   └── utils/            # Utility modules
│       ├── dsstore.py    # DS_Store removal
│       ├── duplicates.py # Duplicate detection (imohash)
│       └── exif.py       # EXIF/ID3/RIFF date extraction
├── pyproject.toml        # Package configuration
├── CHANGELOG.md          # Version history
└── README.md             # This file
```

## License

MIT
