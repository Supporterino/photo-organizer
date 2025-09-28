# photo_organizer/main.py

import argparse
import os
import re
import shutil
import datetime
import logging
import glob
from tqdm import tqdm
import fnmatch
import hashlib
import os.path


def list_files(
    source: str,
    recursive: bool = False,
    file_endings: list | None = None,
    exclude_pattern: str | None = None,
    exclude_is_regex: bool = False,
) -> list[str]:
    """
    Return a list of file paths that satisfy the same criteria used by
    the CLI.  This is deliberately a *pure* function – no side effects,
    no I/O other than the file‑system scan.

    Parameters
    ----------
    source : str
        Root directory to search.
    recursive : bool, default False
        Whether sub‑directories should be traversed.
    file_endings : list[str] | None, default None
        List of extensions to include (e.g. ['.jpg', '.png']).
    exclude_pattern : str | None, default None
        Glob or regex pattern for files that should be omitted.
    exclude_is_regex : bool, default False
        Treat ``exclude_pattern`` as a regular expression if True.

    Returns
    -------
    list[str]
        Absolute file paths that match the criteria.
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


def get_exif_creation_date(file_path):
    """
    Extract creation date from EXIF data if available.

    Returns:
    tuple: (year, month, day) if EXIF data exists and valid, None otherwise
    """
    try:
        import exifread
    except ImportError:
        logging.warning("exifread library not installed. EXIF functionality disabled.")
        return None

    try:
        with open(file_path, 'rb') as f:
            tags = exifread.process_file(f)
    except Exception as e:
        logging.error(f"Error reading EXIF for {file_path}: {e}")
        return None

    # Get EXIF creation date (common tag)
    exif_date = str(tags.get('Image DateTime'))
    if exif_date:
        try:
            # Parse EXIF date string (format: '2023:09:15 14:30:22')
            dt = datetime.datetime.strptime(exif_date, '%Y:%m:%d %H:%M:%S')
            return (dt.year, dt.month, dt.day)
        except (ValueError, TypeError):
            logging.warning(f"Invalid EXIF date format: {exif_date}. Falling back to file system.")
            return None

    return None  # No valid EXIF date found


def get_creation_date(file_path, use_exif=False):
    """
    Get creation date from either EXIF data (if enabled) or file system metadata.

    Parameters:
    file_path (str): Path to file
    use_exif (bool): Whether to use EXIF data for creation date (default: False)

    Returns:
    tuple: (year, month, day) from EXIF or file system creation time
    """
    # If EXIF is requested, try EXIF first
    if use_exif:
        exif_date = get_exif_creation_date(file_path)
        if exif_date:
            return exif_date
        else:
            logging.debug(f"EXIF date not found for {file_path}. Falling back to file system.")

    # Fallback to file system method (no recursion)
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


def _ensure_directory_exists(folder_path):
    """
    Ensure the given folder path exists. If not, create all missing directories.

    Parameters:
    folder_path (str): The path to the folder.
    """
    os.makedirs(folder_path, exist_ok=True)
    logging.debug(f"Ensured directory exists: {folder_path}")


def _configure_logging(verbose):
    """
    Configure logging settings.

    Parameters:
    verbose (int): Increase verbosity with count (max of 2).
    """
    level = logging.WARNING  # default
    if verbose == 1:
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


def _sanitize_path(path: str) -> str:
    """Sanitize path to prevent path traversal attacks."""
    sanitized = os.path.normpath(path)
    # Check for dangerous path components
    if re.search(r'(\.\./|^\.\.\/|^\.\.)', sanitized):
        raise ValueError("Path contains invalid traversal components")
    return sanitized


def _get_file_hash(file_path: str, max_size: int = 100 * 1024 * 1024) -> str:
    """Get MD5 hash of file (for quick duplicate checks)."""
    try:
        # Skip large files (100MB+) to avoid excessive I/O
        if os.path.getsize(file_path) > max_size:
            return "LARGE_FILE"
        with open(file_path, 'rb') as f:
            chunk = f.read(4096)
            if not chunk:
                return None
            hash_obj = hashlib.md5()
            while chunk:
                hash_obj.update(chunk)
                chunk = f.read(4096)
        return hash_obj.hexdigest()
    except Exception as e:
        logging.error(f"Error hashing {file_path}: {e}")
        return None

def _parse_arguments():
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
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run (no actual file operations)",
    )
    parser.add_argument(
        "--exif",
        action="store_true",
        default=False,
        help="Use EXIF data for creation date instead of file system creation time"
    )

    return parser.parse_args()

def organize_files(
    files: list[str],
    target: str,
    *,
    no_progress: bool = False,
    daily: bool = False,
    copy: bool = False,
    no_year: bool = False,
    delete_duplicates: bool = False,
    dry_run: bool = False,
    exif: bool = False,
) -> tuple[int, list[str]]:
    """
    Organise files from *source* into *target* according to the
    provided options.  This function is a drop‑in replacement for the
    CLI logic – it performs **no argument parsing** and returns a
    lightweight result instead of printing to stdout.

    Parameters
    ----------
    files: list[str]
        Files to process.
    target : str
        Directories for output.
    no_progress : bool
        Disable progress bar for usage in a fully automated environment.
    daily : bool
        Create a day folder under month (i.e. YYYY/MM/DD).
    copy : bool
        Copy instead of moving files.
    no_year : bool
        Omit the year level (YYYY‑MM) instead of YYYY/MM.
    delete_duplicates : bool
        Delete source file when an identical target exists.
    dry_run : bool
        Skip all filesystem writes – useful for testing.
    exif : bool
        Prefer EXIF dates over file system timestamps.

    Returns
    -------
    tuple[int, list[str]]
        ``(success_count, failed_files)``
    """
    failed_files = []  # Track files that couldn't be processed
    success_count = 0

    if dry_run:
        logging.info("Dry run mode enabled - no actual file operations will be performed")

    # Precompute directory structure for progress reporting
    directory_counts = {}
    for file_path in files:
        sanitized_path = _sanitize_path(file_path)
        if not sanitized_path:
            logging.warning(f"Skipped invalid path: {file_path}")
            continue
        year, month, day = get_creation_date(sanitized_path, use_exif=exif)
        folder_path = os.path.join(target, f"{year}", f"{month:02d}", f"{day:02d}")
        directory_counts[folder_path] = directory_counts.get(folder_path, 0) + 1

    # Process files with improved duplicate checking
    if no_progress:
        file_iter = files
    else:
        file_iter = tqdm(files, unit="files", desc="Organizing")

    for file_path in file_iter:
        # Sanitize path to prevent traversal attacks
        sanitized_path = _sanitize_path(file_path)
        if not sanitized_path:
            logging.warning(f"Skipped invalid path: {file_path}")
            continue

        year, month, day = get_creation_date(sanitized_path, use_exif=exif)

        # Build target structure (with sanitization)
        folder_parts = [target]
        if no_year:
            folder_parts.append(f"{str(year)}-{month:02d}")
        else:
            folder_parts.append(str(year))
            folder_parts.append(f"{month:02d}")
        if daily:
            folder_parts.append(f"{day:02d}")
        target_folder = os.path.join(*folder_parts)
        _ensure_directory_exists(target_folder)
        target_path = os.path.join(target_folder, os.path.basename(sanitized_path))

        # Check for duplicate (using hash first)
        if os.path.exists(target_path):
            # Check hash first (for large files)
            source_hash = _get_file_hash(file_path)
            target_hash = _get_file_hash(target_path)

            if source_hash == target_hash:
                # Exact match - handle as duplicate
                if delete_duplicates:
                    try:
                        os.remove(file_path)
                        logging.info(f"Deleted duplicate '{file_path}' (matches existing)")
                    except Exception as e:
                        logging.error(f"Error deleting duplicate '{file_path}': {e}")
                        failed_files.append(file_path)
                else:
                    logging.info(f"Skipping '{file_path}': Identical file already exists")
                continue
            else:
                # Different content but same path - error
                logging.error(f"File conflict: '{target_path}' already exists but is different")
                failed_files.append(file_path)
                continue

        # Move or copy (with permission checks)
        try:
            if not os.access(target_folder, os.W_OK):
                raise PermissionError(f"Write permission denied for {target_folder}")

            if not dry_run:
                if copy:
                    # Use copy2 with permission preservation
                    shutil.copy2(file_path, target_path)
                else:
                    # Check write permissions before moving
                    shutil.move(file_path, target_path)

            # Update progress counts
            success_count += 1
            logging.info(f"Processed {file_path} → {target_path}")
        except Exception as e:
            logging.error(f"Error processing {file_path}: {e}")
            failed_files.append(file_path)
        finally:
            # Update directory counts for progress reporting
            if no_progress:
                continue
            if os.path.exists(target_path):
                directory_counts[target_folder] = directory_counts.get(target_folder, 0) + 1

    # Show progress summary
    if file_iter and not no_progress:
        file_iter.close()
    logging.info(
        f"Organized {success_count} files")

    return success_count, failed_files

def main() -> int:
    """Entrypoint used by the console‑script."""
    args = _parse_arguments()
    _configure_logging(args.verbose)

    if not os.path.isdir(args.source):
        logging.error(f"Source directory does not exist: {args.source}")
        return 1

    _ensure_directory_exists(args.target)

    files = list_files(
        source=args.source,
        recursive=args.recursive,
        file_endings=args.endings,
        exclude_pattern=args.exclude,
        exclude_is_regex=args.exclude_regex,
    )

    if not files:
        logging.warning("No matching files found.")
        return 0

    success, failed = organize_files(
        files,
        args.target,
        no_progress=args.no_progress,
        daily=args.daily,
        copy=args.copy,
        no_year=args.no_year,
        delete_duplicates=args.delete_duplicates,
        dry_run=args.dry_run,
        exif=args.exif,
    )

    if failed:
        logging.warning(f"{len(failed)} files could not be processed.")
        return 1
    logging.info("All files organized successfully.")
    return 0

if __name__ == "__main__":
    exit(main())
