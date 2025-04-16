import os
import pytest
import datetime
from unittest import mock
from photo_organizer.main import (
    get_creation_date,
)  # Replace `your_module` with your actual module name


@pytest.fixture
def create_temp_file():
    """Create a temporary file for testing and return its path."""
    with open("temp_test_file.txt", "w") as f:
        f.write("Test content")
    yield "temp_test_file.txt"
    os.remove("temp_test_file.txt")  # Cleanup after test


def test_get_creation_date_mocked_nt():
    """Test get_creation_date on Windows by mocking os.getctime() and os.stat()."""
    with mock.patch("os.name", "nt"), mock.patch(
        "os.path.getctime", return_value=1700000000.0
    ), mock.patch("os.stat"):
        assert get_creation_date("dummy_path") == (2023, 11, 14)


def test_get_creation_date_mocked_macos():
    """Test get_creation_date on macOS by mocking st_birthtime."""
    mock_stat = mock.Mock()
    mock_stat.st_birthtime = 1700000000.0

    with mock.patch("os.stat", return_value=mock_stat):
        assert get_creation_date("dummy_path") == (2023, 11, 14)


def test_get_creation_date_mocked_linux():
    """Test get_creation_date on Linux by falling back to st_mtime."""
    mock_stat = mock.Mock()
    del mock_stat.st_birthtime  # Simulate Linux (no birthtime)
    mock_stat.st_mtime = 1700000000.0

    with mock.patch("os.stat", return_value=mock_stat):
        assert get_creation_date("dummy_path") == (2023, 11, 14)


def test_get_creation_date_real_file(create_temp_file):
    """Test get_creation_date with a real file."""
    file_path = create_temp_file
    year, month, day = get_creation_date(file_path)

    # Ensure the date is today's date (as it's newly created)
    today = datetime.date.today()
    assert (year, month, day) == (today.year, today.month, today.day)
