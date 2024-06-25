import pytest
import os
import tempfile
import shutil
from datetime import datetime
from unittest.mock import patch
from photo_organizer.main import (
    list_files,
    get_creation_date,
    ensure_directory_exists,
    organize_files,
)


@pytest.fixture
def setup_source_directory():
    with tempfile.TemporaryDirectory() as source_dir:
        # Create some test files
        file_paths = [
            os.path.join(source_dir, "photo1.jpg"),
            os.path.join(source_dir, "photo2.png"),
            os.path.join(source_dir, "document.txt"),
        ]
        for file_path in file_paths:
            with open(file_path, "w") as f:
                f.write("test")

        yield source_dir, file_paths


@pytest.fixture
def setup_target_directory():
    with tempfile.TemporaryDirectory() as target_dir:
        yield target_dir


def test_list_files_non_recursive(setup_source_directory):
    source_dir, file_paths = setup_source_directory
    files = list_files(source_dir, recursive=False)
    assert len(files) == 3
    assert all(
        os.path.basename(f) in ["photo1.jpg", "photo2.png", "document.txt"]
        for f in files
    )


def test_list_files_recursive(setup_source_directory):
    source_dir, file_paths = setup_source_directory
    sub_dir = os.path.join(source_dir, "subdir")
    os.makedirs(sub_dir)
    sub_file_path = os.path.join(sub_dir, "subphoto.jpg")
    with open(sub_file_path, "w") as f:
        f.write("test")

    files = list_files(source_dir, recursive=True)
    assert len(files) == 4
    assert any(os.path.basename(f) == "subphoto.jpg" for f in files)


def test_list_files_with_endings(setup_source_directory):
    source_dir, file_paths = setup_source_directory
    files = list_files(source_dir, recursive=False, file_endings=[".jpg"])
    assert len(files) == 1
    assert os.path.basename(files[0]) == "photo1.jpg"


def test_get_creation_date(setup_source_directory):
    source_dir, file_paths = setup_source_directory
    file_path = file_paths[0]
    year, month, day = get_creation_date(file_path)
    now = datetime.now()
    assert year == now.year
    assert month == now.month
    assert day == now.day


def test_ensure_directory_exists():
    with tempfile.TemporaryDirectory() as temp_dir:
        new_dir = os.path.join(temp_dir, "newdir")
        ensure_directory_exists(new_dir)
        assert os.path.exists(new_dir)


@patch("photo_organizer.main.get_creation_date", return_value=(2021, 1, 1))
@patch("photo_organizer.main.shutil.copy2")
def test_organize_files_copy(
    mock_copy, mock_get_creation_date, setup_source_directory, setup_target_directory
):
    source_dir, file_paths = setup_source_directory
    target_dir = setup_target_directory

    class Args:
        def __init__(self):
            self.target = target_dir
            self.daily = False
            self.no_year = False
            self.copy = True

    args = Args()
    organize_files(args, file_paths)

    target_folder = os.path.join(target_dir, "2021", "01")
    target_file_path = os.path.join(target_folder, "photo1.jpg")
    assert os.path.exists(target_folder)
    assert mock_copy.called


@patch("photo_organizer.main.get_creation_date", return_value=(2021, 1, 1))
@patch("photo_organizer.main.shutil.move")
def test_organize_files_move(
    mock_move, mock_get_creation_date, setup_source_directory, setup_target_directory
):
    source_dir, file_paths = setup_source_directory
    target_dir = setup_target_directory

    class Args:
        def __init__(self):
            self.target = target_dir
            self.daily = False
            self.no_year = False
            self.copy = False

    args = Args()
    organize_files(args, file_paths)

    target_folder = os.path.join(target_dir, "2021", "01")
    target_file_path = os.path.join(target_folder, "photo1.jpg")
    assert os.path.exists(target_folder)
    assert mock_move.called


@patch("photo_organizer.main.get_creation_date", return_value=(2021, 1, 1))
@patch("photo_organizer.main.shutil.move")
def test_organize_files_no_year(
    mock_move, mock_get_creation_date, setup_source_directory, setup_target_directory
):
    source_dir, file_paths = setup_source_directory
    target_dir = setup_target_directory

    class Args:
        def __init__(self):
            self.target = target_dir
            self.daily = False
            self.no_year = True
            self.copy = False

    args = Args()
    organize_files(args, file_paths)

    target_folder = os.path.join(target_dir, "2021-01")
    target_file_path = os.path.join(target_folder, "photo1.jpg")
    assert os.path.exists(target_folder)
    assert mock_move.called


@patch("photo_organizer.main.get_creation_date", return_value=(2021, 1, 1))
@patch("photo_organizer.main.shutil.move")
def test_organize_files_daily(
    mock_move, mock_get_creation_date, setup_source_directory, setup_target_directory
):
    source_dir, file_paths = setup_source_directory
    target_dir = setup_target_directory

    class Args:
        def __init__(self):
            self.target = target_dir
            self.daily = True
            self.no_year = False
            self.copy = False

    args = Args()
    organize_files(args, file_paths)

    target_folder = os.path.join(target_dir, "2021", "01", "01")
    target_file_path = os.path.join(target_folder, "photo1.jpg")
    assert os.path.exists(target_folder)
    assert mock_move.called


@patch("photo_organizer.main.get_creation_date", return_value=(2021, 1, 1))
@patch("photo_organizer.main.shutil.move")
def test_organize_files_no_year_daily(
    mock_move, mock_get_creation_date, setup_source_directory, setup_target_directory
):
    source_dir, file_paths = setup_source_directory
    target_dir = setup_target_directory

    class Args:
        def __init__(self):
            self.target = target_dir
            self.daily = True
            self.no_year = True
            self.copy = False

    args = Args()
    organize_files(args, file_paths)

    target_folder = os.path.join(target_dir, "2021-01", "01")
    target_file_path = os.path.join(target_folder, "photo1.jpg")
    assert os.path.exists(target_folder)
    assert mock_move.called
