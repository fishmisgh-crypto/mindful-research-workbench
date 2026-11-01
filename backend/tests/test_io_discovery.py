"""SYNTHETIC — NOT STUDY DATA. Session and block discovery and ordering (D5, D6)."""

from pathlib import Path

from mindful.io.discovery import discover, discover_participant


def make_dirs(root: Path, *rel: str) -> None:
    for r in rel:
        (root / r).mkdir(parents=True)


def test_sessions_sorted_numerically_and_dir_order_recorded(tmp_path: Path) -> None:
    make_dirs(tmp_path, "T5/day_9/Block_01", "T5/day_10/Block_01", "T5/day_100/Block_01")
    p = discover_participant(tmp_path, "T5")
    assert p.chronological_order == ("day_9", "day_10", "day_100")
    assert p.matlab_dir_order == ("day_10", "day_100", "day_9")
    assert not p.dir_order_matches_chronological
    assert [s.index for s in p.sessions] == [1, 2, 3]


def test_equal_width_day_numbers_keep_dir_order(tmp_path: Path) -> None:
    make_dirs(tmp_path, "T11/day_800/Block_03", "T11/day_658/Block_05", "T11/day_751/Block_16")
    assert discover_participant(tmp_path, "T11").dir_order_matches_chronological


def test_blocks_sorted_by_number_and_junk_ignored(tmp_path: Path) -> None:
    make_dirs(tmp_path, "T11/day_658/Block_07", "T11/day_658/Block_05", "T11/day_658/notes")
    (tmp_path / "T11/day_658/.DS_Store").write_text("")
    (tmp_path / "T11/day_658/Block_05/data.mat").write_text("")
    session = discover_participant(tmp_path, "T11").sessions[0]
    assert [b.number for b in session.blocks] == [5, 7]
    assert session.blocks[0].missing_files == ("task.mat", "info.mat")
    assert "day_658/.DS_Store" in discover_participant(tmp_path, "T11").ignored_entries


def test_only_expected_participants_discovered(tmp_path: Path) -> None:
    make_dirs(tmp_path, "T11/day_1/Block_01", "T11(additional)/random_targets/day_665/Block_08")
    assert list(discover(tmp_path)) == ["T11"]
