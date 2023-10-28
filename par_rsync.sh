#!/bin/bash

source_folder="/mnt/nas/backup_10/Pictures/"
destination_folder="/mnt/nas/Pictures"
cores=24

# Function to sync a single directory
sync_directory() {
    rsync -avh --dry-run --progress --ignore-existing  "$1" "$2"
}

export -f sync_directory

# Use GNU Parallel to sync folders in parallel
find /mnt/nas/backup_10/Pictures/ -type f -printf "%P\n" | \
    parallel -0 -j"$cores" sync_directory {} "$destination_folder"

echo "Synchronization completed."
