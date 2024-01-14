# dry run to output only the files that would sync or moves
rsync -av --dry-run --progress --ignore-existing  /mnt/nas/backup_06/Pictures/ /mnt/nas/Pictures/ > /mnt/nas/backup_06/rsync_dryrun_14JAN24.txt

rsync -av --dry-run --progress --ignore-existing  /mnt/nas/backup_07/Pictures/ /mnt/nas/Pictures/ > /mnt/nas/backup_07/rsync_dryrun_14JAN24.txt

rsync -av --dry-run --progress --ignore-existing  /mnt/nas/backup_10/Pictures/ /mnt/nas/Pictures/ > /mnt/nas/backup_10/rsync_dryrun_14JAN24.txt

# sorted foldes to pictures
rsync -av --dry-run --progress --ignore-existing  /mnt/nas/TEST_SORT_OUTPUT/ /mnt/nas/Pictures/ > /mnt/nas/TEST_SORT_OUTPUT/rsync_dryrun_14JAN24.txt

rsync -av --dry-run --progress --ignore-existing  /mnt/nas/TEST_SORT_OUTPUT2/ /mnt/nas/Pictures/ > /mnt/nas/TEST_SORT_OUTPUT2/rsync_dryrun_14JAN24.txt

# sync files and delete from source once copied
rsync -av --remove-source-files --progress --ignore-existing  /mnt/nas/test_sort/ /mnt/nas/Pictures/