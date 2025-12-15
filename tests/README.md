# Media Sorter Test Suite

Comprehensive pytest test suite for the media-sorter package with 153 passing tests.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py          # Shared fixtures and test utilities
├── test_cli.py          # CLI argument parsing and command tests (40 tests)
├── test_sorter.py       # MediaFileSorter class tests (35 tests)
├── test_exif.py         # EXIF date extraction tests (33 tests)
├── test_dsstore.py      # DS_Store file removal tests (18 tests)
└── test_duplicates.py   # Duplicate file detection tests (27 tests)
```

## Running Tests

### Run all tests
```bash
pytest tests/ -v
```

### Run specific test file
```bash
pytest tests/test_exif.py -v
```

### Run specific test class
```bash
pytest tests/test_sorter.py::TestMediaFileSorter -v
```

### Run specific test
```bash
pytest tests/test_exif.py::TestParseDatetimeFromString::test_parse_standard_exif_date -v
```

### Run with coverage
```bash
pytest tests/ --cov=media_sorter --cov-report=html
```

## Test Coverage

### test_cli.py (40 tests)
Tests CLI functionality including:
- `parse_date()` - Date string parsing with validation
- `confirm_action()` - User confirmation prompts
- `cmd_sort()` - Sort command with all options (copy/move, dry-run, date ranges)
- `cmd_clean()` - DS_Store cleanup command
- `cmd_dedup()` - Duplicate removal command
- `main()` - Main CLI entry point with argument parsing

### test_sorter.py (35 tests)
Tests MediaFileSorter class including:
- `check_exiftool()` - ExifTool availability verification
- Initialization and validation
- `_apply_day_begins()` - Day start time adjustment logic
- `_is_in_date_range()` - Date range filtering
- `_get_folder_name()` - Folder name generation with custom formats
- File operations (copy/move, dry-run, duplicate handling)
- Error handling (no date, processing errors)
- Empty folder cleanup

### test_exif.py (33 tests)
Tests EXIF date extraction utilities:
- `parse_datetime_from_string()` - Parse EXIF date strings
  - Standard formats: "2023:12:25 14:30:22"
  - Edge cases: "0000-00-00", empty strings, invalid dates
  - Timezone and millisecond handling
- `extract_date_from_filename()` - Extract dates from filenames
  - Patterns: IMG_20231225_143022.jpg, VID_20231225.mp4
  - ISO formats: 2023-12-25_photo.jpg
  - Date validation (year range 1990-2100)
- `get_media_date()` - Combined EXIF + filename extraction
  - Priority: EXIF metadata > filename pattern
  - AAE sidecar file handling
  - Fallback behavior

### test_dsstore.py (18 tests)
Tests DS_Store file utilities:
- `find_ds_store_files()` - Locate .DS_Store and ._.DS_Store files
  - Recursive directory traversal
  - Non-existent directory handling
- `remove_ds_store_file()` - Single file removal
- `remove_ds_store_files()` - Batch removal
  - Verbose/quiet modes
  - Permission error handling
  - Preservation of non-DS_Store files

### test_duplicates.py (27 tests)
Tests duplicate file detection:
- `DuplicateFileRemover` class
  - `hash_file()` - Consistent file hashing using imohash
  - `find_duplicates()` - Duplicate detection
  - `remove_duplicates()` - Removal keeping shortest filename
  - `get_removed_count()` - Accurate counting
- `remove_duplicates_in_directory()` - Batch processing
  - Subdirectory processing
  - Dry-run mode
  - Cross-subdirectory isolation

## Fixtures (conftest.py)

### Directory Fixtures
- `temp_source_dir` - Temporary source directory
- `temp_dest_dir` - Temporary destination directory

### File Fixtures
- `sample_image_file` - IMG_20231225_143022.jpg
- `sample_video_file` - VID_20231225_153045.mp4
- `sample_audio_file` - VN_20231225_143022.m4a
- `sample_file_no_date` - random_photo.jpg
- `sample_files_with_dates` - Multiple files with various date patterns
- `sample_duplicate_files` - Two files with identical content

### Mock Fixtures
- `mock_exiftool_success` - Mock successful exiftool execution
- `mock_exiftool_not_found` - Mock exiftool not found
- `mock_exiftool_metadata` - Mock ExifToolHelper with sample metadata
- `mock_exiftool_no_date` - Mock ExifToolHelper without date
- `mock_exiftool_error` - Mock ExifToolHelper raising error

## Test Design Principles

1. **No External Dependencies**: Tests mock exiftool calls - no actual exiftool required
2. **Isolated**: Each test uses temporary directories via pytest's `tmp_path`
3. **Fast**: No real media files needed, all tests run in under 1 second
4. **Comprehensive Edge Cases**: Invalid dates, permission errors, malformed data
5. **Parametrized**: Uses `pytest.mark.parametrize` for testing multiple inputs
6. **Well-Documented**: Every test has a descriptive docstring

## Common Test Patterns

### Testing with mocked ExifTool
```python
def test_example(sample_image_file, mock_exiftool_metadata):
    result = get_media_date(str(sample_image_file))
    assert result == datetime(2023, 12, 25, 14, 30, 22)
```

### Testing file operations
```python
def test_example(temp_source_dir, temp_dest_dir):
    sorter = MediaFileSorter(str(temp_source_dir), str(temp_dest_dir))
    sorter.process_file(str(sample_file))
    assert dest_file.exists()
```

### Testing CLI commands
```python
def test_example(monkeypatch):
    with patch.object(sys, "argv", ["media-sorter", "sort", "source", "dest"]):
        main()
```

## Known Warnings

- One deprecation warning from tqdm using `datetime.utcfromtimestamp()` (external dependency)
