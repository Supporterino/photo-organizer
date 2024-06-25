# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
