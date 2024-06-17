# tests/test_main.py

import os
import pytest
import tempfile
import datetime
from photo_organizer.main import list_files, get_creation_date, ensure_directory_exists

def test_list_files_non_recursive():
    with tempfile.TemporaryDirectory() as tmpdirname:
        # Create test files
        file1 = os.path.join(tmpdirname, "file1.txt")
        file2 = os.path.join(tmpdirname, "file2.txt")
        with open(file1, 'w') as f:
            f.write("test")
        with open(file2, 'w') as f:
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
        with open(file1, 'w') as f:
            f.write("test")
        with open(file2, 'w') as f:
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
