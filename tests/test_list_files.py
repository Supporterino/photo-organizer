import os
import re
import pytest
import shutil
from tempfile import TemporaryDirectory
from photo_organizer.main import list_files


@pytest.fixture
def setup_test_directory():
    """Create a temporary test directory with sample files."""
    with TemporaryDirectory() as temp_dir:
        # Create some test files
        test_files = [
            "file1.txt",
            "file2.log",
            "image.jpg",
            "photo.png",
            "document.pdf",
            "notes.TXT",
            "script.PY",
            "archive.zip",
            "trashfile.tmp",
        ]
        subdir = os.path.join(temp_dir, "subdir")
        os.makedirs(subdir)

        for file in test_files:
            with open(os.path.join(temp_dir, file), "w") as f:
                f.write("test")

        # Add files to subdirectory
        with open(os.path.join(subdir, "nested.txt"), "w") as f:
            f.write("nested test")

        yield temp_dir  # Provide the directory to tests


def test_list_files_non_recursive(setup_test_directory):
    """Test listing files in a non-recursive manner."""
    temp_dir = setup_test_directory
    files = list_files(temp_dir)

    assert len(files) == 9  # Only top-level files
    assert os.path.join(temp_dir, "file1.txt") in files
    assert os.path.join(temp_dir, "image.jpg") in files


def test_list_files_recursive(setup_test_directory):
    """Test recursive listing of files."""
    temp_dir = setup_test_directory
    files = list_files(temp_dir, recursive=True)

    assert len(files) == 10  # Includes nested.txt
    assert os.path.join(temp_dir, "subdir", "nested.txt") in files


def test_list_files_with_extensions(setup_test_directory):
    """Test filtering files by extensions."""
    temp_dir = setup_test_directory
    files = list_files(temp_dir, file_endings=[".txt", ".jpg"])

    assert len(files) == 3  # file1.txt, notes.TXT, and image.jpg
    assert os.path.join(temp_dir, "file1.txt") in files
    assert os.path.join(temp_dir, "image.jpg") in files
    assert os.path.join(temp_dir, "notes.TXT") in files


def test_list_files_exclude_regex(setup_test_directory):
    """Test excluding files using a regex pattern."""
    temp_dir = setup_test_directory
    files = list_files(temp_dir, exclude_pattern=r".*\.log", exclude_is_regex=True)

    assert len(files) == 8  # Excludes file2.log
    assert os.path.join(temp_dir, "file2.log") not in files


def test_list_files_exclude_glob(setup_test_directory):
    """Test excluding files using a glob pattern."""
    temp_dir = setup_test_directory
    files = list_files(temp_dir, exclude_pattern="*trash*", exclude_is_regex=False)

    assert len(files) == 8  # Excludes trashfile.tmp
    assert not any("trashfile" in f for f in files)


def test_list_files_empty_directory():
    """Test behavior with an empty directory."""
    with TemporaryDirectory() as empty_dir:
        files = list_files(empty_dir)
        assert files == []  # Should return an empty list


def test_list_files_case_insensitive_extensions(setup_test_directory):
    """Ensure file extensions are handled case-insensitively."""
    temp_dir = setup_test_directory
    files = list_files(temp_dir, file_endings=[".txt"])

    assert os.path.join(temp_dir, "file1.txt") in files
    assert os.path.join(temp_dir, "notes.TXT") in files  # Should still be included


def test_list_files_combined_filters(setup_test_directory):
    """Test both file extension filtering and exclusion regex together."""
    temp_dir = setup_test_directory
    files = list_files(
        temp_dir,
        file_endings=[".txt", ".log"],
        exclude_pattern=r"file2.*",
        exclude_is_regex=True,
    )

    assert len(files) == 2  # Excludes file2.log
    assert os.path.join(temp_dir, "file1.txt") in files
    assert os.path.join(temp_dir, "notes.TXT") in files
