from os import path, remove, walk
import concurrent.futures
from argparse import ArgumentParser

def remove_ds_store_file(file_path):
    try:
        remove(file_path)
        return f"Removed '{file_path}'"
    except Exception as e:
        return f"Error removing '{file_path}': {str(e)}"

def remove_ds_store_files(directory):
    # Ensure the directory exists
    if not path.exists(directory):
        print(f"Directory '{directory}' does not exist.")
        return

    ds_store_files = []

    # Use scandir() to directly list files in the directory
    ds_store_files = [path.join(root, filename) for root, _, files in walk(directory) for filename in files if filename == '.DS_Store']

    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(executor.map(remove_ds_store_file, ds_store_files))

    for result in results:
        print(result)

if __name__ == "__main__":

    # Create a command-line argument parser
    parser = ArgumentParser(description="Remove '.DS_Store' files from a directory.")

    # Add a positional argument for the directory path
    parser.add_argument("directory", help="The directory to search for '.DS_Store' files.")

    # Parse the command-line arguments
    args = parser.parse_args()

    # Call the function to remove '.DS_Store' files in parallel
    remove_ds_store_files(args.directory)

