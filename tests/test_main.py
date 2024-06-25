# tests/test_main.py

import argparse
import os
import pytest
import tempfile
from photo_organizer.main import (
    list_files,
    get_creation_date,
    ensure_directory_exists,
    main,
)
import shutil
import datetime
from unittest.mock import patch


def test_list_files_non_recursive():
    with tempfile.TemporaryDirectory() as tmpdirname:
        # Create test files
        file1 = os.path.join(tmpdirname, "file1.txt")
        file2 = os.path.join(tmpdirname, "file2.txt")
        with open(file1, "w") as f:
            f.write("test")
        with open(file2, "w") as f:
            f.write("test")

        # Call the function
        result = list_files(tmpdirname, recursive=False)

        # Assert the results
        assert len(result) == 2
        assert file1 in result
        assert file2 in result


def test_list_files_recursive():
    with tempfile.TemporaryDirectory() as tmpdirname:
        # Create test files and directories
        subdir = os.path.join(tmpdirname, "subdir")
        os.makedirs(subdir)
        file1 = os.path.join(tmpdirname, "file1.txt")
        file2 = os.path.join(subdir, "file2.txt")
        with open(file1, "w") as f:
            f.write("test")
        with open(file2, "w") as f:
            f.write("test")

        # Call the function
        result = list_files(tmpdirname, recursive=True)

        # Assert the results
        assert len(result) == 2
        assert file1 in result
        assert file2 in result


def test_get_creation_date():
    with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
        tmpfile.write(b"test")
        tmpfile_name = tmpfile.name

    try:
        year, month, day = get_creation_date(tmpfile_name)

        now = datetime.datetime.now()
        assert year == now.year
        assert month == now.month
        assert day == now.day
    finally:
        os.remove(tmpfile_name)


def test_ensure_directory_exists():
    with tempfile.TemporaryDirectory() as tmpdirname:
        new_dir = os.path.join(tmpdirname, "newdir")

        # Call the function
        ensure_directory_exists(new_dir)

        # Assert the results
        assert os.path.exists(new_dir)
        assert os.path.isdir(new_dir)

        # Call the function again to ensure it does not raise an error
        ensure_directory_exists(new_dir)
        assert os.path.exists(new_dir)
        assert os.path.isdir(new_dir)


@pytest.mark.parametrize(
    "daily,no_year,expected_folder",
    [
        (False, False, "{year}/{month:02d}"),
        (False, True, "{year}-{month:02d}"),
        (True, False, "{year}/{month:02d}/{day:02d}"),
        (True, True, "{year}-{month:02d}/{day:02d}"),
    ],
)
def test_folder_structure(daily, no_year, expected_folder):
    with tempfile.TemporaryDirectory() as source_dir, tempfile.TemporaryDirectory() as target_dir:
        # Create a test file
        file_path = os.path.join(source_dir, "testfile.txt")
        with open(file_path, "w") as f:
            f.write("test")

        year, month, day = get_creation_date(file_path)
        expected_folder = expected_folder.format(year=year, month=month, day=day)

        # Run the script
        with patch(
            "argparse.ArgumentParser.parse_args",
            return_value=argparse.Namespace(
                source=source_dir,
                target=target_dir,
                recursive=False,
                daily=daily,
                endings=None,
                verbose=False,
                copy=False,
                no_year=no_year,
            ),
        ):
            main()

        # Check if the file was moved to the correct folder
        target_folder = os.path.join(target_dir, expected_folder)
        target_file_path = os.path
