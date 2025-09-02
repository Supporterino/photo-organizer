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
import fnmatch


def list_files(
    source,
    recursive=False,
    file_endings=None,
    exclude_pattern=None,
    exclude_is_regex=False,
):
    """
    List all files in the source directory, optionally filtering by file extension
    and excluding files using glob or regex patterns.

    Parameters:
    source (str): The source directory path.
    recursive (bool): If True, list files recursively. Default is False.
    file_endings (list): List of file extensions to include (e.g., ['.jpg', '.png']). Default is None.
    exclude_pattern (str): A glob or regex pattern to exclude matching files. Default is None.
    exclude_is_regex (bool): Whether to treat the exclude_pattern as a regular expression.

    Returns:
    list: A list of file paths that meet the criteria.
    """
    pattern = None
    if exclude_pattern:
        try:
            pattern_str = (
                exclude_pattern
                if exclude_is_regex
                else fnmatch.translate(exclude_pattern)
            )
            pattern = re.compile(pattern_str)
            logging.debug(
                f"Using {'regex' if exclude_is_regex else 'glob'} exclude pattern: '{exclude_pattern}' "
                f"-> compiled regex: '{pattern.pattern}'"
            )
        except re.error as e:
            logging.error(f"Invalid exclude pattern '{exclude_pattern}': {e}")
            return []

    file_endings = tuple(e.lower() for e in file_endings) if file_endings else None

    # Use glob for efficient file listing
    search_pattern = os.path.join(source, "**" if recursive else "*")
    all_files = glob.glob(search_pattern, recursive=recursive)

    file_list = [
        file
        for file in all_files
        if os.path.isfile(file)
        and (not file_endings or file.lower().endswith(file_endings))
        and (not pattern or not pattern.search(os.path.basename(file)))
    ]

    logging.debug(
        f"Listed {len(file_list)} files from {source} (recursive={recursive})"
    )
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
    verbose (int): Increase verbosity with count (max of 2).
    """
    if verbose == 0:
        level = logging.WARNING  # default
    elif verbose == 1:
        level = logging.INFO
    elif verbose == 2:
        level = logging.DEBUG
    elif verbose > 2:
        level = logging.DEBUG
        logging.warning("Verbosity set >2 has no effect.")

    logging.basicConfig(
        level=level,
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
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity level (use -v for verbose, -vv for more verbose).",
    )
    parser.add_argument(
        "-c", "--copy", action="store_true", help="Copy files instead of moving them"
    )
    parser.add_argument(
        "--no-year",
        action="store_true",
        help="Do not place month folders inside a year folder",
    )
    parser.add_argument(
        "--exclude",
        help="Glob or regex pattern to exclude files. Defaults to glob unless --exclude-regex is set.",
    )
    parser.add_argument(
        "--exclude-regex",
        action="store_true",
        help="Interpret the --exclude pattern as a regular expression.",
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable progress bar for usage in a fully automated environment.",
    )
    parser.add_argument(
        "--delete-duplicates",
        action="store_true",
        help="Delete source file if an identical file already exists in the target directory",
    )

    return parser.parse_args()


def organize_files(args, files):
    """
    Organize files by moving or copying them to the target directory.

    Parameters:
    args (Namespace): Parsed command line arguments.
    files (list): List of file paths to organize.
    """
    failed_files = []  # Track files that couldn't be processed

    if args.no_progress:
        file_iter = files
    else:
        file_iter = tqdm(files, unit="files")

    for file_path in file_iter:
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
                if args.delete_duplicates:
                    try:
                        os.remove(file_path)
                        logging.info(
                            f"Deleted duplicate '{file_path}' (already exists at '{target_path}')"
                        )
                    except Exception as e:
                        logging.error(f"Error deleting duplicate '{file_path}': {e}")
                        failed_files.append(file_path)
                else:
                    logging.warning(
                        f"Skipping '{file_path}': Identical file already exists at '{target_path}'"
                    )
                continue
            else:
                logging.error(
                    f"File conflict: '{target_path}' already exists but is different."
                )
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
        exclude_is_regex=args.exclude_regex,
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
