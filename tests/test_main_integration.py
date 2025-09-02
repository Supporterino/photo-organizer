import os
import tempfile
from pathlib import Path
import pytest
from photo_organizer.main import main


@pytest.fixture
def setup_temp_dirs():
    with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as target:
        Path(src, "photo1.jpg").write_text("test 1")
        Path(src, "photo2.png").write_text("test 2")
        Path(src, "notes.txt").write_text("not a photo")
        yield {"source": src, "target": target, "files": list(Path(src).iterdir())}


def mock_args(base, **overrides):
    class Args:
        source = base["source"]
        target = base["target"]
        copy = False
        no_year = False
        no_progress = False
        daily = False
        recursive = False
        endings = [".jpg", ".png"]
        exclude = None
        verbose = 0
        exclude_regex = False

    for key, value in overrides.items():
        setattr(Args, key, value)
    return Args


def apply_basic_monkeypatch(monkeypatch, args):
    monkeypatch.setattr("photo_organizer.main.parse_arguments", lambda: args)
    monkeypatch.setattr(
        "photo_organizer.main.get_creation_date", lambda path: (2024, 4, 4)
    )


def test_move_files(monkeypatch, setup_temp_dirs):
    args = mock_args(setup_temp_dirs)
    apply_basic_monkeypatch(monkeypatch, args)
    exit_code = main()
    target = Path(args.target) / "2024" / "04"
    assert exit_code == 0
    assert sorted(f.name for f in target.iterdir()) == ["photo1.jpg", "photo2.png"]


def test_copy_files(monkeypatch, setup_temp_dirs):
    args = mock_args(setup_temp_dirs, copy=True)
    apply_basic_monkeypatch(monkeypatch, args)
    exit_code = main()
    target = Path(args.target) / "2024" / "04"
    assert exit_code == 0
    assert sorted(f.name for f in target.iterdir()) == ["photo1.jpg", "photo2.png"]
    assert Path(setup_temp_dirs["source"], "photo1.jpg").exists()


def test_daily_structure(monkeypatch, setup_temp_dirs):
    args = mock_args(setup_temp_dirs, daily=True)
    apply_basic_monkeypatch(monkeypatch, args)
    exit_code = main()
    target = Path(args.target) / "2024" / "04" / "04"
    assert exit_code == 0
    assert sorted(f.name for f in target.iterdir()) == ["photo1.jpg", "photo2.png"]


def test_no_year(monkeypatch, setup_temp_dirs):
    args = mock_args(setup_temp_dirs, no_year=True)
    apply_basic_monkeypatch(monkeypatch, args)
    exit_code = main()
    target = Path(args.target) / "2024-04"
    assert exit_code == 0
    assert sorted(f.name for f in target.iterdir()) == ["photo1.jpg", "photo2.png"]


def test_no_year_daily(monkeypatch, setup_temp_dirs):
    args = mock_args(setup_temp_dirs, no_year=True, daily=True)
    apply_basic_monkeypatch(monkeypatch, args)
    exit_code = main()
    target = Path(args.target) / "2024-04" / "04"
    assert exit_code == 0
    assert sorted(f.name for f in target.iterdir()) == ["photo1.jpg", "photo2.png"]


def test_exclude_pattern(monkeypatch, setup_temp_dirs):
    args = mock_args(setup_temp_dirs, exclude="photo2", exclude_regex=True)
    apply_basic_monkeypatch(monkeypatch, args)
    exit_code = main()
    target = Path(args.target) / "2024" / "04"
    assert exit_code == 0
    assert [f.name for f in target.iterdir()] == ["photo1.jpg"]


def test_filter_by_endings(monkeypatch, setup_temp_dirs):
    args = mock_args(setup_temp_dirs, endings=[".png"])
    apply_basic_monkeypatch(monkeypatch, args)
    exit_code = main()
    target = Path(args.target) / "2024" / "04"
    assert exit_code == 0
    assert [f.name for f in target.iterdir()] == ["photo2.png"]
