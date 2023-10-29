#!/bin/bash

source_folder="/mnt/nas/source"
destination_folder="/mnt/nas/dest"
cores=24

# Function to sync a single directory
sync_directory() {
    rsync -avh --progress --ignore-existing  "$1" "$2"
}

export -f sync_directory

# Use GNU Parallel to sync folders in parallel
find "$source_folder" -type f -printf "%P\n" | \
    parallel -0 -j"$cores" sync_directory {} "$destination_folder"

echo "Synchronization completed."

# regular rsync 9.319 sec
# time parallel -j 10 --eta rsync -a {} /mnt/nas/dest/ ::: /mnt/nas/source/*
# find /mnt/nas/TEST_PAR_RSYNC/source/ -type f -printf "%P\n" | split -l $(($(wc -l < /dev/stdin) / 3)) - split_
