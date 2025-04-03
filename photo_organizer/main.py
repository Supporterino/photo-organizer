# photo_organizer/main.py

import argparse
import os
import re
import shutil
import datetime
import logging
import filecmp


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
    file_list = []
    pattern = re.compile(exclude_pattern) if exclude_pattern else None
    
    if recursive:
        for root, dirs, files in os.walk(source):
            for file in files:
                if (not file_endings or file.lower().endswith(tuple(file_endings))) and (not pattern or not pattern.search(file)):
                    file_list.append(os.path.join(root, file))
    else:
        with os.scandir(source) as entries:
            for entry in entries:
                if entry.is_file() and (not file_endings or entry.name.lower().endswith(tuple(file_endings))) and (not pattern or not pattern.search(entry.name)):
                    file_list.append(entry.path)
    
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
    if os.name == "nt":  # Windows
        creation_time = os.path.getctime(file_path)
    else:  # macOS or Linux
        stat = os.stat(file_path)
        try:
            creation_time = stat.st_birthtime
        except AttributeError:
            # Fallback to the last metadata change time (best approximation)
            creation_time = stat.st_mtime

    creation_date = datetime.datetime.fromtimestamp(creation_time)
    year = creation_date.year
    month = creation_date.month
    day = creation_date.day

    logging.debug(f"File {file_path} creation date: {year}-{month:02d}-{day:02d}")
    return year, month, day


def ensure_directory_exists(folder_path):
    """
    Check if a given folder path exists, if not, create all missing folders.

    Parameters:
    folder_path (str): The path to the folder.
    """
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        logging.info(f"Created missing directories for path: {folder_path}")
    else:
        logging.debug(f"Directory already exists: {folder_path}")


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
    for file_path in files:
        year, month, day = get_creation_date(file_path)
        if args.no_year:
            if args.daily:
                target_folder = os.path.join(
                    args.target, f"{year}-{month:02d}", f"{day:02d}"
                )
            else:
                target_folder = os.path.join(args.target, f"{year}-{month:02d}")
        else:
            if args.daily:
                target_folder = os.path.join(
                    args.target, str(year), f"{month:02d}", f"{day:02d}"
                )
            else:
                target_folder = os.path.join(args.target, str(year), f"{month:02d}")

        ensure_directory_exists(target_folder)
        target_path = os.path.join(target_folder, os.path.basename(file_path))

        if os.path.exists(target_path):
            if filecmp.cmp(file_path, target_path, shallow=False):
                logging.warning(
                    f"File '{target_path}' already exists and is identical. Skipping."
                )
                continue
            else:
                logging.error(
                    f"File '{target_path}' already exists and is different. Aborting."
                )
                return

        try:
            if args.copy:
                shutil.copy2(file_path, target_path)
                logging.info(f"Copied '{file_path}' to '{target_path}'")
            else:
                shutil.move(file_path, target_path)
                logging.info(f"Moved '{file_path}' to '{target_path}'")
        except Exception as e:
            logging.error(
                f"Failed to {'copy' if args.copy else 'move'} '{file_path}' to '{target_path}': {e}"
            )
            return


def main():
    """
    Main entry point for the photo organizer script. Parses arguments, configures logging, and processes files.
    """
    # Parse the arguments
    args = parse_arguments()
    
    # Configure logging
    configure_logging(args.verbose)
    
    logging.info("Starting file sorting process")
    
    # Ensure the source directory exists
    if not os.path.exists(args.source):
        logging.error(f"Source directory '{args.source}' does not exist.")
        return
    
    # Ensure the target directory exists
    ensure_directory_exists(args.target)
    
    # List all files in the source directory, applying the exclusion filter
    files = list_files(args.source, args.recursive, args.endings, args.exclude)
    
    # Organize files by moving or copying them to the target directory
    organize_files(args, files)
