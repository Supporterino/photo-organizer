# photo_organizer/main.py

import argparse
import os
import re
import shutil
import datetime
import logging
import filecmp
import glob
from tqdm import tqdm

def list_files(source, recursive=False, file_endings=None, exclude_pattern=None):
    """
    List all files in the source directory, optionally filtering by file extension and excluding files by regex.

    Parameters:
    source (str): The source directory path.
    recursive (bool): If True, list files recursively. Default is False.
    file_endings (list): List of file extensions to include (e.g., ['.jpg', '.png']). Default is None.
    exclude_pattern (str): A regex pattern to exclude matching files. Default is None.

    Returns:
    list: A list of file paths that meet the criteria.
    """
    pattern = re.compile(exclude_pattern) if exclude_pattern else None
    file_endings = tuple(e.lower() for e in file_endings) if file_endings else None
    
    # Use glob for efficient file listing
    search_pattern = os.path.join(source, "**" if recursive else "*")
    all_files = glob.glob(search_pattern, recursive=recursive)

    file_list = [
        file for file in all_files
        if os.path.isfile(file)  # Ensure it's a file
        and (not file_endings or file.lower().endswith(file_endings))  # Filter by extension
        and (not pattern or not pattern.search(os.path.basename(file)))  # Apply regex exclusion
    ]

    logging.debug(f"Listed {len(file_list)} files from {source}, excluding pattern: {exclude_pattern}")
    return file_list


def get_creation_date(file_path):
    """
    Get the creation date of a file and extract year, month, and day.

    Parameters:
    file_path (str): The path to the file.

    Returns:
    tuple: A tuple containing the year, month, and day.
    """
    stat = os.stat(file_path)

    if os.name == "nt":  # Windows
        creation_time = os.path.getctime(file_path)
    elif hasattr(stat, "st_birthtime"):  # macOS
        creation_time = stat.st_birthtime
    else:  # Linux (fallback to last metadata change time)
        creation_time = stat.st_mtime

    creation_date = datetime.date.fromtimestamp(creation_time)

    logging.debug(f"File {file_path} creation date: {creation_date}")
    return creation_date.year, creation_date.month, creation_date.day


def ensure_directory_exists(folder_path):
    """
    Ensure the given folder path exists. If not, create all missing directories.

    Parameters:
    folder_path (str): The path to the folder.
    """
    os.makedirs(folder_path, exist_ok=True)
    logging.debug(f"Ensured directory exists: {folder_path}")


def configure_logging(verbose):
    """
    Configure logging settings.

    Parameters:
    verbose (bool): If True, enable verbose logging.
    """
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )


def parse_arguments():
    """
    Parse command-line arguments for the photo organizer.

    Returns:
    argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Sort photos from source to target directory."
    )
    parser.add_argument("source", type=str, help="The source directory")
    parser.add_argument("target", type=str, help="The target directory")
    parser.add_argument("-r", "--recursive", action="store_true", help="Sort photos recursively")
    parser.add_argument("-d", "--daily", action="store_true", default=False, help="Folder structure with daily folders")
    parser.add_argument("-e", "--endings", type=str, nargs="*", help="File endings/extensions to copy (e.g., .jpg .png)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("-c", "--copy", action="store_true", help="Copy files instead of moving them")
    parser.add_argument("--no-year", action="store_true", help="Do not place month folders inside a year folder")
    parser.add_argument("--exclude", type=str, help="Regex pattern to exclude files from processing")
    
    return parser.parse_args()


def organize_files(args, files):
    """
    Organize files by moving or copying them to the target directory.

    Parameters:
    args (Namespace): Parsed command line arguments.
    files (list): List of file paths to organize.
    """
    failed_files = []  # Track files that couldn't be processed

    for file_path in tqdm(files, unit='files'):
        year, month, day = get_creation_date(file_path)
        
        # Construct target folder structure
        folder_parts = [args.target]
        if args.no_year:
            folder_parts.append(f"{str(year)}-{month:02d}")
        else:
            folder_parts.append(str(year))
            folder_parts.append(f"{month:02d}")
        if args.daily:
            folder_parts.append(f"{day:02d}")

        target_folder = os.path.join(*folder_parts)
        ensure_directory_exists(target_folder)
        target_path = os.path.join(target_folder, os.path.basename(file_path))

        # Check for duplicate file
        if os.path.exists(target_path):
            if filecmp.cmp(file_path, target_path, shallow=False):
                logging.warning(f"Skipping '{file_path}': Identical file already exists at '{target_path}'")
                continue
            else:
                logging.error(f"File conflict: '{target_path}' already exists but is different.")
                failed_files.append(file_path)
                continue

        # Move or copy file
        try:
            if args.copy:
                shutil.copy2(file_path, target_path)
                logging.info(f"Copied '{file_path}' → '{target_path}'")
            else:
                shutil.move(file_path, target_path)
                logging.info(f"Moved '{file_path}' → '{target_path}'")
        except Exception as e:
            logging.error(f"Error moving/copying '{file_path}' → '{target_path}': {e}")
            failed_files.append(file_path)

    return failed_files  # Return failed files for better handling

def main():
    """
    Main entry point for the photo organizer script.
    Parses arguments, configures logging, and processes files.
    """
    args = parse_arguments()
    configure_logging(args.verbose)

    logging.info("Photo Organizer started")
    
    if not os.path.isdir(args.source):
        logging.error(f"Source directory does not exist: {args.source}")
        return 1  # Exit with error

    ensure_directory_exists(args.target)

    logging.info("Collecting files...")
    files = list_files(
        source=args.source,
        recursive=args.recursive,
        file_endings=args.endings,
        exclude_pattern=args.exclude,
    )

    if not files:
        logging.warning("No matching files found to organize.")
        return 0  # Exit normally, nothing to do

    logging.info(f"{len(files)} files found. Starting organization...")
    failed = organize_files(args, files)

    if failed:
        logging.warning(f"Organization completed with {len(failed)} failed file(s).")
        return 1  # Partial failure
    else:
        logging.info("All files organized successfully.")
        return 0

