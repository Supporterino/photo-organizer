import os
import pytest
from unittest import mock
from photo_organizer.main import main  # Adjust import path as needed


@pytest.fixture
def mock_args():
    """Mocked argparse.Namespace for main tests."""
    return mock.Mock(
        source="/mock/source",
        target="/mock/target",
        recursive=False,
        endings=None,
        exclude=None,
        copy=False,
        no_year=False,
        daily=False,
        verbose=0,
    )


def test_main_source_does_not_exist(mock_args):
    with mock.patch(
        "photo_organizer.main.parse_arguments", return_value=mock_args
    ), mock.patch("photo_organizer.main.configure_logging"), mock.patch(
        "photo_organizer.main.os.path.isdir", return_value=False
    ):
        result = main()
        assert result == 1


def test_main_no_files_found(mock_args):
    with mock.patch(
        "photo_organizer.main.parse_arguments", return_value=mock_args
    ), mock.patch("photo_organizer.main.configure_logging"), mock.patch(
        "photo_organizer.main.os.path.isdir", return_value=True
    ), mock.patch(
        "photo_organizer.main.ensure_directory_exists"
    ), mock.patch(
        "photo_organizer.main.list_files", return_value=[]
    ):
        result = main()
        assert result == 0


def test_main_all_files_success(mock_args):
    with mock.patch(
        "photo_organizer.main.parse_arguments", return_value=mock_args
    ), mock.patch("photo_organizer.main.configure_logging"), mock.patch(
        "photo_organizer.main.os.path.isdir", return_value=True
    ), mock.patch(
        "photo_organizer.main.ensure_directory_exists"
    ), mock.patch(
        "photo_organizer.main.list_files", return_value=["file1.jpg", "file2.jpg"]
    ), mock.patch(
        "photo_organizer.main.organize_files", return_value=[]
    ):
        result = main()
        assert result == 0


def test_main_with_failures(mock_args):
    with mock.patch(
        "photo_organizer.main.parse_arguments", return_value=mock_args
    ), mock.patch("photo_organizer.main.configure_logging"), mock.patch(
        "photo_organizer.main.os.path.isdir", return_value=True
    ), mock.patch(
        "photo_organizer.main.ensure_directory_exists"
    ), mock.patch(
        "photo_organizer.main.list_files", return_value=["file1.jpg", "file2.jpg"]
    ), mock.patch(
        "photo_organizer.main.organize_files", return_value=["file2.jpg"]
    ):
        result = main()
        assert result == 1
