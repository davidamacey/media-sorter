# Media File Sorter

The Media File Sorter is a Python script that organizes media files (e.g., photos and videos) based on their creation date. It can be especially useful for managing large collections of media files that lack proper organization. The script can process multiple files concurrently to improve efficiency.

Using this script, speed depends on hardware.  Using 24 cores and a local NAS, processing 18000 photos and videos totalling about 175 GB completed in about 8 minutes.

## Prerequisites

Before using the script, ensure that you have the following dependencies installed:

- Python 3.11
- The `exiftool` library

You can install the required Python libraries using `pip`:

```bash
pip install -r requirements.txt
```
### Download iPhone Photos to NAS

Purpose is to copy files from iPhone device directly to the local NAS file storage

## Connect iPhone

Connect iPhone via USB connection and login via Ubuntu

1. Turn off WiFi and Bluetooth, turn on Personal Hotspot
2. Navigate to the network section of Files.
3. Remove the `:3/` from the address to connect to iPhone system.  

## Find Files to Copy

Options:
1. Manually go through iPhone DCIM folder and NAS Picture files and find latest file by date and select items to copy.
2. Use a script (to be created) to find the latest file in NAS to select newer files on iPhone.

Copy files to an import folder on the NAS:

Select the DCIM folder and select the folders you would like to copy, then drop and drop to copy.

## Workflow

Intent to is to run each script individually with human in the loop.

1. Run 'sort_img.py' script to organize media from source by YYYY-MM-DD format
2. Run 'remove_dsstore.py' script to remove the .DS_Store file from camera
3. Run 'remove_dupes.py' script to remove the duplicate files within each sub folder given a directory.
4. Run 'rsync' command to merge new media to master media directory, 'rsync -avh --progress --ignore-existing /source/folder/ /desitnation/folder'

## Usage - Sorting by YYYY-MM-DD

To sort your media files, run the script as follows:

Using the year month day sorting method, run the script: `sort_img3.py` to move the files accordingly.

**IMPORTANT NOTE:** This will by default move files and remove from source during copy process.  Reduces duplicate files and consolidates to single photo directory.

Run Script:
```bash
time python sort_img.py /mnt/nas/import_pictures/ /mnt/nas/Pictures/ ./iphone_transfer_<date>.txt
```

- `source_dir`: The source directory containing your unsorted media files.
- `dest_dir`: The destination directory where the sorted files will be placed.
- `log_file`: The output log file to record the sorting process and statistics.

## Removing `.DS_Store` Files

### Description

The `.DS_Store` file remover is a Python script designed to remove all `.DS_Store` files from a directory. These files are commonly created on macOS systems and can clutter your directories when transferred to non-macOS systems.

### Usage

To remove `.DS_Store` files, run the script as follows:

```bash
python remove_ds_store.py directory
```

- `directory`: The directory in which you want to remove `.DS_Store` files.

## Removing Duplicate Files

### Description

The Duplicate File Remover is a Python script designed to find and remove duplicate files within a directory. It uses the SHA-256 hash of files to identify duplicates and provides the option to perform a dry run, allowing you to see what would be removed without actually deleting files.

Use Case: Folders with duplicate files, but with different file names such as IMG_0001.JPG and IMG_0001-1.JPG.  Checks for duplicate hash, if so removes file.

### Prerequisites

Before using the script, ensure that you have the following dependencies installed:

- Python 3.11

### Usage

To remove duplicate files, run the script as follows:

```bash
python remove_dupes.py directory [--dry-run]
```

- `directory`: The directory in which you want to find and remove duplicate files.
- `--dry-run` (optional): Print what would be removed without deleting files. Use this flag for a trial run.


## Synchronizing Folders

### Description

The folder synchronization via CLI that uses the `rsync` command to synchronize files from a source folder to a destination folder. It can be used to keep two directories in sync efficiently. Please make sure you have `rsync` installed on your system.

```bash
rsync -avh --progress --ignore-existing /source/folder/ /desitnation/folder'
```