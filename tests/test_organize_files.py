import os
import pytest
import shutil
import filecmp
import tempfile
from unittest import mock
from photo_organizer.main import (
    organize_files,
    get_creation_date,
)  # Replace `your_module` with your actual module name


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing and return its path."""
    with tempfile.TemporaryDirectory() as temp_folder:
        yield temp_folder  # Provide the temp folder to the test


@pytest.fixture
def sample_files(temp_dir):
    """Create sample files with dummy content."""
    file1 = os.path.join(temp_dir, "file1.txt")
    file2 = os.path.join(temp_dir, "file2.txt")

    with open(file1, "w") as f:
        f.write("Test file 1")
    with open(file2, "w") as f:
        f.write("Test file 2")

    return [file1, file2]


def test_organize_files_move(temp_dir, sample_files):
    """Test moving files into the organized structure."""
    args = mock.Mock()
    args.target = os.path.join(temp_dir, "organized")
    args.copy = False
    args.no_year = False
    args.daily = False

    with mock.patch(
        "photo_organizer.main.get_creation_date", return_value=(2023, 11, 14)
    ):
        failed_files = organize_files(args, sample_files)

    # Ensure the files were moved
    expected_path1 = os.path.join(args.target, "2023", "11", "file1.txt")
    expected_path2 = os.path.join(args.target, "2023", "11", "file2.txt")

    assert os.path.exists(expected_path1)
    assert os.path.exists(expected_path2)
    assert not os.path.exists(sample_files[0])  # Original file should be gone
    assert not os.path.exists(sample_files[1])
    assert failed_files == []


def test_organize_files_copy(temp_dir, sample_files):
    """Test copying files instead of moving."""
    args = mock.Mock()
    args.target = os.path.join(temp_dir, "organized")
    args.copy = True
    args.no_year = False
    args.daily = False

    with mock.patch(
        "photo_organizer.main.get_creation_date", return_value=(2023, 11, 14)
    ):
        failed_files = organize_files(args, sample_files)

    # Ensure the files were copied
    expected_path1 = os.path.join(args.target, "2023", "11", "file1.txt")
    expected_path2 = os.path.join(args.target, "2023", "11", "file2.txt")

    assert os.path.exists(expected_path1)
    assert os.path.exists(expected_path2)
    assert os.path.exists(sample_files[0])  # Original file should still exist
    assert os.path.exists(sample_files[1])
    assert failed_files == []


def test_organize_files_conflict_identical(temp_dir, sample_files):
    """Test handling of duplicate identical files."""
    args = mock.Mock()
    args.target = os.path.join(temp_dir, "organized")
    args.copy = True
    args.no_year = False
    args.daily = False

    target_file = os.path.join(args.target, "2023", "11", "file1.txt")
    os.makedirs(os.path.dirname(target_file), exist_ok=True)
    shutil.copy2(sample_files[0], target_file)  # Create identical file

    with mock.patch(
        "photo_organizer.main.get_creation_date", return_value=(2023, 11, 14)
    ):
        failed_files = organize_files(args, sample_files)

    assert failed_files == []  # Should skip identical files without errors


def test_organize_files_conflict_different(temp_dir, sample_files):
    """Test handling of duplicate but different files."""
    args = mock.Mock()
    args.target = os.path.join(temp_dir, "organized")
    args.copy = True
    args.no_year = False
    args.daily = False

    target_file = os.path.join(args.target, "2023", "11", "file1.txt")
    os.makedirs(os.path.dirname(target_file), exist_ok=True)

    with open(target_file, "w") as f:
        f.write("Different content")  # Create different file with the same name

    with mock.patch(
        "photo_organizer.main.get_creation_date", return_value=(2023, 11, 14)
    ):
        failed_files = organize_files(args, sample_files)

    assert failed_files == [sample_files[0]]  # Different file should cause failure


def test_organize_files_daily(temp_dir, sample_files):
    """Test organizing files with daily structure."""
    args = mock.Mock()
    args.target = os.path.join(temp_dir, "organized")
    args.copy = False
    args.no_year = False
    args.daily = True

    with mock.patch(
        "photo_organizer.main.get_creation_date", return_value=(2023, 11, 14)
    ):
        failed_files = organize_files(args, sample_files)

    # Ensure the files were moved into daily folders
    expected_path1 = os.path.join(args.target, "2023", "11", "14", "file1.txt")
    expected_path2 = os.path.join(args.target, "2023", "11", "14", "file2.txt")

    assert os.path.exists(expected_path1)
    assert os.path.exists(expected_path2)
    assert failed_files == []


def test_organize_files_no_year(temp_dir, sample_files):
    """Test organizing files without a year folder."""
    args = mock.Mock()
    args.target = os.path.join(temp_dir, "organized")
    args.copy = False
    args.no_year = True
    args.daily = False

    with mock.patch(
        "photo_organizer.main.get_creation_date", return_value=(2023, 11, 14)
    ):
        failed_files = organize_files(args, sample_files)

    # Ensure the files were moved into a structure without a year
    expected_path1 = os.path.join(args.target, "2023-11", "file1.txt")
    expected_path2 = os.path.join(args.target, "2023-11", "file2.txt")

    assert os.path.exists(expected_path1)
    assert os.path.exists(expected_path2)
    assert failed_files == []
