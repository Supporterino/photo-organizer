# photo_organizer/main.py

import argparse
import os
import shutil
import datetime
import logging


def list_files(source, recursive=False, file_endings=None):
    """
    List all files in the source directory.

    Parameters:
    source (str): The source directory path.
    recursive (bool): If True, list files recursively. Default is False.
    file_endings (list): List of file endings/extensions to include. Default is None.

    Returns:
    list: A list of file paths.
    """
    file_list = []
    if recursive:
        for root, dirs, files in os.walk(source):
            for file in files:
                if not file_endings or file.lower().endswith(tuple(file_endings)):
                    file_list.append(os.path.join(root, file))
    else:
        with os.scandir(source) as entries:
            for entry in entries:
                if entry.is_file() and (
                    not file_endings or entry.name.lower().endswith(tuple(file_endings))
                ):
                    file_list.append(entry.path)
    logging.debug(f"Listed {len(file_list)} files from {source}")
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


def main():
    # Set up the argument parser
    parser = argparse.ArgumentParser(
        description="Sort photos from source to target directory."
    )
    parser.add_argument("source", type=str, help="The source directory")
    parser.add_argument("target", type=str, help="The target directory")
    parser.add_argument(
        "-r", "--recursive", action="store_true", help="Sort photos recursively"
    )
    parser.add_argument(
        "-d",
        "--daily",
        action="store_true",
        default=False,
        help="Folder structure with daily folders",
    )
    parser.add_argument(
        "-e",
        "--endings",
        type=str,
        nargs="*",
        help="File endings/extensions to copy (e.g., .jpg .png)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument(
        "-c", "--copy", action="store_true", help="Copy files instead of moving them"
    )

    # Parse the arguments
    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    logging.info("Starting file sorting process")

    # Ensure the source directory exists
    if not os.path.exists(args.source):
        logging.error(f"Source directory '{args.source}' does not exist.")
        return

    # Ensure the target directory exists
    ensure_directory_exists(args.target)

    # List all files in the source directory
    files = list_files(args.source, args.recursive, args.endings)

    # Move or copy files to the target directory organized by year/month (and optionally day)
    for file_path in files:
        year, month, day = get_creation_date(file_path)
        if args.daily:
            target_folder = os.path.join(
                args.target, str(year), f"{month:02d}", f"{day:02d}"
            )
        else:
            target_folder = os.path.join(args.target, str(year), f"{month:02d}")
        ensure_directory_exists(target_folder)
        target_path = os.path.join(target_folder, os.path.basename(file_path))

        if args.copy:
            # Copy the file
            shutil.copy2(file_path, target_path)
            logging.info(f"Copied '{file_path}' to '{target_path}'")
        else:
            # Move the file
            shutil.move(file_path, target_path)
            logging.info(f"Moved '{file_path}' to '{target_path}'")
