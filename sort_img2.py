from os import makedirs, path, walk
from shutil import copy2, copystat
from concurrent.futures import ThreadPoolExecutor
from argparse import ArgumentParser
from hashlib import md5
import logging
from exiftool import ExifToolHelper
from datetime import datetime
from tqdm import tqdm
from shutil import move

class MediaFileSorter:
    def __init__(self, source_dir, dest_dir, num_workers, log_file):
        self.source_dir = source_dir
        self.dest_dir = dest_dir
        self.num_workers = num_workers
        self.log_file = log_file

        self.total_files_copied = 0
        self.files_copied_by_type = {}
        
        self.if_move = True
        
        self.dry_run = False
        
        self.no_date_folder = None
        self.error_folder = None

    def create_destination_folders(self):
        makedirs(self.dest_dir, exist_ok=True)
        self.no_date_folder = path.join(self.dest_dir, "00_no_date_found")
        makedirs(self.no_date_folder, exist_ok=True)
        self.error_folder = path.join(self.dest_dir, "00_media_error")
        makedirs(self.error_folder, exist_ok=True)
        
    def get_media_date(self, file):
        date = None
        try:
            with ExifToolHelper() as et:
                output = et.get_metadata(file)[0]
        except:
            return None
        
        # Handle video files specifically
        # if file.lower().endswith(('.mov', '.mp4', '.avi')):  # Add other video formats as needed
        if 'QuickTime:CreationDate' in output:
            date_str = output['QuickTime:CreationDate']
            # Parse the date and time along with the timezone
            try:
                date = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S%z').astimezone()
            except ValueError:
                date = None
        elif'EXIF:CreateDate' in output:
                date_str = output['EXIF:CreateDate']
                try:
                    date = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                except ValueError:
                    date = None
        elif'EXIF:DateTimeOriginal' in output:
                date_str = output['EXIF:DateTimeOriginal']
                try:
                    date = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                except ValueError:
                    date = None
        elif output.get('File:FileModifyDate'):
            date = output.get('File:FileModifyDate')
            date = datetime.strptime(date, '%Y:%m:%d %H:%M:%S%z').astimezone()
        else:
            date = None
            
        # Return the date or none
        if date:
            return date.strftime('%Y-%m-%d %H:%M:%S')
        else:
            return None

    def copy_file(self, file):
        try:
            date_taken = self.get_media_date(file)

            if date_taken:
                new_date = datetime.strptime(date_taken.split(' ')[0], "%Y-%m-%d")

                date_folder = new_date.strftime("%Y-%m-%d")
                dest_folder = path.join(self.dest_dir, date_folder)
                makedirs(dest_folder, exist_ok=True)

                current_folder = path.dirname(file)
                base_name, ext = path.splitext(path.basename(file))
                dest_file = path.join(dest_folder, path.basename(file))

                # Check if the file is already in the correct folder
                if current_folder == dest_folder:
                    # The file is in the correct folder, no action needed
                    return

                # Handling duplicate file names
                counter = 1
                new_file_hash = md5(open(file, 'rb').read()).hexdigest()
                while path.exists(dest_file):
                    existing_file_hash = md5(open(dest_file, 'rb').read()).hexdigest()

                    if new_file_hash != existing_file_hash:
                        dest_file = path.join(dest_folder, f"{base_name}_{counter}{ext}")
                        counter += 1
                    else:
                        # File already exists with the same content
                        return
                
                if not self.dry_run:
                    if self.if_move:
                        move(file, dest_file)
                    else:
                        copy2(file, dest_file)
                        copystat(file, dest_file)
                    
                self.total_files_copied += 1
                ext = path.splitext(file)[1]
                self.files_copied_by_type[ext] = self.files_copied_by_type.get(ext, 0) + 1
            else:
                # Handle files with no date
                self.handle_no_date_file(file)
        except Exception as e:
            self.handle_error_file(file, e)

    def handle_no_date_file(self, file):
        # dest_file = path.join(self.no_date_folder, path.basename(file))
        # if not self.dry_run:
        #     if self.if_move:
        #         move(file, dest_file)
        #     else:
        #         copy2(file, dest_file)
        #         copystat(file, dest_file)
            
        # self.total_files_copied += 1
        # self.files_copied_by_type['no_date'] = self.files_copied_by_type.get('no_date', 0) + 1
        
        logging.info(f'NO DATE FILE: {file}')

    def handle_error_file(self, file, error):
        logging.error(f"Error processing {file}: {str(error)}")
        # dest_file = path.join(self.error_folder, path.basename(file))
        # if not self.dry_run:
        #     if self.if_move:
        #         move(file, dest_file)
        #     else:
        #         copy2(file, dest_file)
        #         copystat(file, dest_file)
                
        # self.total_files_copied += 1
        # self.files_copied_by_type['error'] = self.files_copied_by_type.get('error', 0) + 1
        
    def sort_media_files(self):
        self.create_destination_folders()
        
        # List of common video file extensions (add or remove as needed)
        # video_extensions = {'.mp4', '.mov', '.aae'}
        
        # media_files = [path.join(root, filename)
        #                    for root, _, files in walk(self.source_dir)
        #                    for filename in files
        #                    if path.splitext(filename)[1].lower() in video_extensions]
        
        media_files = [path.join(root, filename) for root, _, files in walk(self.source_dir) for filename in files]
        
        print(f'There are {len(media_files)} files to look through!')

        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            
            
            # Using tqdm to wrap around the executor.map function to display a progress bar
            for _ in tqdm(executor.map(self.copy_file, media_files), total=len(media_files)):
                pass

        with open(self.log_file, 'w') as log:
            log.write(f"Total Files Copied: {self.total_files_copied}\n")
            for ext, count in self.files_copied_by_type.items():
                log.write(f"Files with Extension {ext}: {count}\n")
            print(f"Media files sorted into '{self.dest_dir}'. Log written to '{self.log_file}'.")

def main():
    parser = ArgumentParser(description="Sort media files based on date taken.")
    parser.add_argument("source_dir", help="Source directory containing media files.")
    parser.add_argument("dest_dir", help="Destination directory for sorted files.")
    parser.add_argument("num_threads", type=int, help="Number of threads for concurrent processing")
    parser.add_argument("log_file", help="Output log file")

    args = parser.parse_args()

    sorter = MediaFileSorter(args.source_dir, args.dest_dir, args.num_threads, args.log_file)
    sorter.sort_media_files()

if __name__ == "__main__":
    logging.basicConfig(filename='media_sorter.log', level=logging.INFO)
    main()


# command python sort_img.py /mnt/nas/unsorted_photos_to_import/import_pictures_9MAR-2/ /mnt/nas/unsorted_photos_to_import/TEST_SORT_OUTPUT/ 45  /mnt/nas/unsorted_photos_to_import/test_sort_output.txt
# command python sort_img.py '/mnt/nas/unsorted_photos_to_import/DJI AIR Drone Dragon 13SEP20/' /mnt/nas/unsorted_photos_to_import/TEST_SORT_OUTPUT/ 45  /mnt/nas/unsorted_photos_to_import/test_sort_output-dji.txt
# time python sort_img.py /mnt/nas/unsorted_photos_to_import/ /mnt/nas/TEST_SORT_OUTPUT/ 47 /mnt/nas/test_sort_output.txt
