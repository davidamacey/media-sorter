from argparse import ArgumentParser
from hashlib import sha256
from os import listdir, path, walk, remove
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
from tqdm import tqdm
import logging

# Configure the logging module to save logs to a file
logging.basicConfig(filename='remove_dupes.log', level=logging.INFO)

class DuplicateFileRemover:
    def __init__(self):
        self.file_hashes = defaultdict(list)
        self.dry_run = False

    def hash_file(self, file_path):
        """Calculate the sha256 hash of a file using hashlib."""
        
        # TODO: Use faster hashing algoritm to speed up processing
        
        hasher = sha256()
        with open(file_path, 'rb') as f:
            data = f.read()
            hasher.update(data)
        return hasher.hexdigest()
    
    def _hash_and_store(self, file_path):
        """Hash a file and store it in the dictionary."""
        file_hash = self.hash_file(file_path)
        self.file_hashes[file_hash].append(file_path)
    
    def remove_file(self, path):
        """Remove a file and log the action."""
        if self.dry_run:
            logging.info(f"Would remove duplicate: {path}")
        else:
            try:
                remove(path)
                logging.info(f"Removed duplicate: {path}")
            except Exception as e:
                logging.error(f"Error removing {path}: {e}")
    
    def find_duplicates(self, directory):
        """Find duplicate files in the specified directory."""
        with ThreadPoolExecutor() as executor:
            file_paths = [path.join(root, file) for root, _, files in walk(directory) for file in files]
            executor.map(self._hash_and_store, file_paths)

    def remove_duplicates(self):
        """Remove duplicate files, keeping the shortest filenames."""
        duplicates = {hash: paths for hash, paths in self.file_hashes.items() if len(paths) > 1}
        with ThreadPoolExecutor() as executor:
            for paths in duplicates.values():
                paths.sort(key=len)
                executor.map(self.remove_file, paths[1:])
    
    def process_directories(self, directory):
        """Process subdirectories within the specified directory."""
        subdirectories = [path.join(directory, d) for d in listdir(directory) if path.isdir(path.join(directory, d))]
    
        pbar = tqdm(total=len(subdirectories))
        for subdir in subdirectories:
            sub_remover = DuplicateFileRemover()
            sub_remover.dry_run = self.dry_run
            sub_remover.find_duplicates(subdir)
            sub_remover.remove_duplicates()
            
            # Calculate and log the total number of files and removed files
            removed_files = sum(len(paths) - 1 for paths in sub_remover.file_hashes.values() if len(paths) > 1)
            logging.info(f"Number of files removed: {removed_files}")
    
            pbar.update(1)  # Update the progress bar
        pbar.close()             
    

def main():
    parser = ArgumentParser(description="Find and remove duplicate files in a directory.")
    parser.add_argument("directory", help="The directory to search for duplicate files.")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be removed without deleting files.")
    args = parser.parse_args()

    remover = DuplicateFileRemover()
    remover.dry_run = args.dry_run
    remover.process_directories(args.directory)
    
    logging.info(f"Finished checking for duplicate files in: {args.directory}")

if __name__ == "__main__":
    main()

# python remove_dupes.py /mnt/nas/TEST_SORT_OUTPUT/ --dry-run