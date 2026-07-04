from pathlib import Path

from app.git_reader import read_git_state


def test_non_git_path_is_graceful(tmp_path: Path) -> None:
    state = read_git_state(str(tmp_path))

    assert state.is_repo is False
    assert state.dirty_files == 0
    assert state.latest_commit is None
    assert state.dirty_file_names == []
