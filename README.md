# Media File Sorter

## Description

The Media File Sorter is a Python script that organizes media files (e.g., photos and videos) based on their creation date. It can be especially useful for managing large collections of media files that lack proper organization. The script can process multiple files concurrently to improve efficiency.

## Prerequisites

Before using the script, ensure that you have the following dependencies installed:

- Python 3.10
- The `exiftool` library

You can install the required Python libraries using `pip`:

```bash
pip install -r requirements.txt
```

## Workflow

Intent to is to run each script individually with human in the loop.

1. Run 'sort_img.py' script to organize media from source by YYYY-MM-DD format
2. Run 'remove_dsstore.py' script to remove the .DS_Store file from camera
3. Run 'remove_dupes.py' script to remove the duplicate files within each sub folder given a directory.
4. Run 'rsync' command to merge new media to master media directory, 'rsync -avh --progress --ignore-existing /source/folder/ /desitnation/folder'

## Usage

To sort your media files, run the script as follows:

```bash
python sort_img.py source_dir dest_dir num_threads log_file
```

- `source_dir`: The source directory containing your unsorted media files.
- `dest_dir`: The destination directory where the sorted files will be placed.
- `num_threads`: The number of threads for concurrent processing (adjust this based on your system's capabilities).
- `log_file`: The output log file to record the sorting process and statistics.

## Example

Sorting media files in `/mnt/nas/unsorted_photos_to_import/` into `/mnt/nas/TEST_SORT_OUTPUT/` using 47 threads:

```bash
python sort_img.py /mnt/nas/unsorted_photos_to_import/ /mnt/nas/TEST_SORT_OUTPUT/ 47 /mnt/nas/test_sort_output.txt
```

## Removing `.DS_Store` Files

### Description

The `.DS_Store` file remover is a Python script designed to remove all `.DS_Store` files from a directory. These files are commonly created on macOS systems and can clutter your directories when transferred to non-macOS systems.

### Usage

To remove `.DS_Store` files, run the script as follows:

```bash
python remove_ds_store.py directory
```

- `directory`: The directory in which you want to remove `.DS_Store` files.

### Example

Remove `.DS_Store` files from a directory:

```bash
python remove_ds_store.py /mnt/nas/your_directory/
```

## Removing Duplicate Files

### Description

The Duplicate File Remover is a Python script designed to find and remove duplicate files within a directory. It uses the SHA-256 hash of files to identify duplicates and provides the option to perform a dry run, allowing you to see what would be removed without actually deleting files.

### Prerequisites

Before using the script, ensure that you have the following dependencies installed:

- Python 3.10

### Usage

To remove duplicate files, run the script as follows:

```bash
python remove_dupes.py directory [--dry-run]
```

- `directory`: The directory in which you want to find and remove duplicate files.
- `--dry-run` (optional): Print what would be removed without deleting files. Use this flag for a trial run.

### Example

Remove duplicate files from a directory:

```bash
python remove_dupes.py /mnt/nas/your_directory/
```

Remove duplicate files from a directory with a dry run:

```bash
python remove_dupes.py /mnt/nas/your_directory/ --dry-run
```

## Synchronizing Folders

### Description

The folder synchronization script is a Bash script that uses the `rsync` command to synchronize files from a source folder to a destination folder. It can be used to keep two directories in sync efficiently. Please make sure you have `rsync` installed on your system.

### Usage

1. Edit the script to set your source folder, destination folder, and the number of CPU cores to utilize for parallel synchronization.

2. Run the script:

```bash
./sync_folders.sh
```

### Example

Edit the script to specify your source and destination folders, and the number of CPU cores, and then run the script.