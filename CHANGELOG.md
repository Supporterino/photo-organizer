# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2025-04-07

### Added

- Full integration test suite covering:
  - Default file moving behavior.
  - `--copy` mode.
  - `--daily` and `--no-year` folder structures.
  - `--exclude` pattern filtering.
  - File extension filtering via `--endings`.
- Extensive `pytest` unit tests for all core utility functions, including:
  - `get_creation_date`
  - `list_files`
  - `organize_files`
  - `ensure_directory_exists`
  - `main`

### Changed

- Optimized all major functions for performance, readability, and maintainability:
  - `list_files`: Reduced I/O overhead and improved filtering logic.
  - `get_creation_date`: Cleaner cross-platform support with clearer logging.
  - `ensure_directory_exists`: Simplified directory creation using `exist_ok=True`.
  - `organize_files`: Restructured for better flow and reduced redundant checks.
  - `main`: Modularized and made return codes explicit for testability.
- Logging improvements across all modules for better traceability during execution.

## [1.2.0] - 2024-04-03

### Added

- New `--exclude` option to allow filtering out files based on a regex pattern.
  - Example: `photo-organizer /path/to/source /path/to/target --exclude "^ignore|\.tmp$"`
  - This helps exclude unwanted files like temporary files or specific naming patterns.
- Updated documentation to reflect the new feature.
- Added unit tests for the `--exclude` functionality.

## [1.1.1] - 2024-06-25

### Changed

- Refactored the `main` function to improve code modularity and readability by extracting logical components into separate functions.

### Added

- Unit tests for core functions using `pytest`.

### Fixed

- Improved logging messages for better debugging and clarity during file operations.

## [1.1.0] - 2024-06-25

### Added

- New optional flag `--no-year` to place month folders top-level with the format `YEAR-MONTH` instead of inside a year folder.
- The `--no-year` option also supports daily folder structure, creating a `YEAR-MONTH/DAY` folder structure.

## [1.0.0] - 2024-06-17

### Added

- Initial release of Photo Organizer.
- Move photos from a source directory to a target directory organized by year and month.
- Support for recursive file search with the `-r`, `--recursive` flag.
- Option to organize photos into daily folders with the `-d`, `--daily` flag.
- Filter photos by file extensions with the `-e`, `--endings` flag.
- Enable verbose logging with the `-v`, `--verbose` flag.
- New optional flag `-c`, `--copy` to copy files instead of moving them. The default behavior remains to move files.
