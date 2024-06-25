# Photo Organizer
[![Tests](https://github.com/Supporterino/photo-organizer/actions/workflows/python-package.yml/badge.svg)](https://github.com/Supporterino/photo-organizer/actions/workflows/python-package.yml)[![Upload Release](https://github.com/Supporterino/photo-organizer/actions/workflows/python-publish.yml/badge.svg)](https://github.com/Supporterino/photo-organizer/actions/workflows/python-publish.yml)[![PyPI version](https://badge.fury.io/py/photo-organizer.svg)](https://badge.fury.io/py/photo-organizer)

Photo Organizer is a Python script that sorts photos from a source directory into a target directory based on their creation date. The script can organize photos into year, month, and optionally day subfolders. It also supports copying or moving files, recursive directory traversal, and filtering by file extensions.

## Features

* Organize photos into year/month/day folders based on creation date
* Move or copy files from the source to the target directory
* Recursively traverse directories
* Filter files by specified extensions
* Verbose logging for detailed information
* Flexible folder structure with optional top-level year-month folders.

## Usage

### Prerequisites

* Python 3.x

### Installation

Install the package using pip:

```bash
pip install photo-organizer
```

### Running the Script

```bash
photo-organizer [-h] [-r] [-d] [-e [ENDINGS [ENDINGS ...]]] [-v] [-c] [--no-year] source target
```

### Arguments

* SOURCE_DIRECTORY: The source directory containing the photos
* TARGET_DIRECTORY: The target directory where the photos will be organized

Options

* `-r`, `--recursive`: Sort photos recursively from the source directory
* `-d`, `--daily`: Organize photos into daily folders (year/month/day)
* `-e`, `--endings`: Specify file endings/extensions to copy (e.g., .jpg .png). If not specified, all files are included
* `-v`, `--verbose`: Enable verbose logging
* `-c`, `--copy`: Copy files instead of moving them
* `--no-year`: Do not place month folders inside a year folder; place them top-level with the name format YEAR-MONTH

### Examples

Move all files from source to target, organizing by year and month:
```bash
photo_organizer /path/to/source /path/to/target
```

Move all files recursively and organize by year/month/day:
```bash
photo_organizer /path/to/source /path/to/target -r -d
```

Copy only .jpg and .png files:
```bash
photo_organizer /path/to/source /path/to/target -e .jpg .png -c
```

Enable verbose logging:
```bash
photo_organizer /path/to/source /path/to/target -v
```

Move photos to top-level year-month folders without a year parent folder:
```bash
photo-organizer --no-year /path/to/source /path/to/target
```

Combine options to copy .jpg and .png files recursively into daily folders with verbose logging:
```bash
photo-organizer -r -d -e .jpg .png -v -c /path/to/source /path/to/target
```

## Dwevelopment

To contribute to this project, follow these steps:

1. Clone the repository.
2. Install dependencies.
3. Make your changes and add tests.
4. Submit a pull request.

## Logging

The script uses Python's logging module to provide detailed information about the operations performed. By default, the logging level is set to INFO. Use the `-v` or `--verbose` flag to enable `DEBUG` level logging for more detailed output.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes. Ensure that your code adheres to the existing coding standards and includes appropriate tests.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
