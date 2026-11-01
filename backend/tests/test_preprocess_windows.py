"""SYNTHETIC — NOT STUDY DATA. Window index vs literal 1-based ports of the MATLAB code."""

import numpy as np
import pytest

from mindful.preprocess.config import matlab_round
from mindful.preprocess.windows import build_windows

LENGTHS = np.array([1234, 987, 1500, 640, 2001])
SESSIONS = np.array([1, 1, 2, 2, 3])


def matlab_select_epoch(
    lengths: np.ndarray, winlen: int, step: int
) -> tuple[list[int], list[int], list[int]]:
    """SelectEpoch with excludeNonTrials=1, 1-based, written as in MINDFUL.m:120-154."""
    ind: list[int] = []
    seg_per_blk: list[int] = []
    length_selected = 0
    for n in lengths:
        seg = int(np.floor(n / step))
        seg_per_blk.append(seg)
        ind += [length_selected + j * step + 1 for j in range(seg)]
        length_selected += int(n)
    stops = [min(i + winlen - 1, length_selected) for i in ind]
    return ind, stops, seg_per_blk


def matlab_session_segment_inds(
    seg_per_blk: list[int], sessions: np.ndarray, day: tuple[int, ...], winlen: int, step: int
) -> list[int]:
    cs = [0, *np.cumsum(seg_per_blk).tolist()]
    loc = [i + 1 for i, s in enumerate(sessions) if s in day]  # 1-based block numbers
    return list(range(cs[loc[0] - 1] + 1, cs[loc[-1]] - matlab_round(winlen / step) + 1 + 1))


def matlab_set_inds_to_nan(
    seg_per_blk: list[int], sessions: np.ndarray, winlen: int, step: int
) -> list[int]:
    lastn = matlab_round(winlen / step)
    cs = np.cumsum(seg_per_blk).tolist()
    out: list[int] = []
    for day in sorted(set(sessions.tolist())):
        loc = [i + 1 for i, s in enumerate(sessions) if s == day]
        out += list(range(cs[loc[-1] - 1] - lastn + 1, cs[loc[-1] - 1] + 1))
    return out


@pytest.mark.parametrize(("winlen", "step"), [(3000, 500), (3000, 50), (300, 70)])
def test_starts_and_stops_match_select_epoch(winlen: int, step: int) -> None:
    w = build_windows(LENGTHS, SESSIONS, winlen, step)
    ind, stops, seg = matlab_select_epoch(LENGTHS, winlen, step)
    np.testing.assert_array_equal(w.starts + 1, ind)
    np.testing.assert_array_equal(w.stops + 1, stops)
    np.testing.assert_array_equal(w.seg_per_block, seg)


@pytest.mark.parametrize("day", [(1,), (1, 2), (2,), (3,)])
@pytest.mark.parametrize(("winlen", "step"), [(3000, 500), (3000, 50), (300, 70)])
def test_reference_windows_match_get_session_segment_inds(
    day: tuple[int, ...], winlen: int, step: int
) -> None:
    w = build_windows(LENGTHS, SESSIONS, winlen, step)
    ref = matlab_session_segment_inds(w.seg_per_block.tolist(), SESSIONS, day, winlen, step)
    np.testing.assert_array_equal(w.session_reference_windows(day) + 1, ref)


def test_bins_covered_matches_unique_rowcolon() -> None:
    w = build_windows(LENGTHS, SESSIONS, 300, 70)
    windows = w.session_reference_windows((1, 2))
    expected = np.unique(np.concatenate([np.arange(w.starts[i], w.stops[i] + 1) for i in windows]))
    np.testing.assert_array_equal(w.bins_covered(windows), expected)


@pytest.mark.parametrize(("winlen", "step"), [(3000, 500), (3000, 50), (300, 70)])
def test_session_end_windows_match_set_inds_to_nan(winlen: int, step: int) -> None:
    w = build_windows(LENGTHS, SESSIONS, winlen, step)
    ref = matlab_set_inds_to_nan(w.seg_per_block.tolist(), SESSIONS, winlen, step)
    np.testing.assert_array_equal(np.sort(w.session_end_windows() + 1), sorted(ref))


def test_reference_drops_one_fewer_window_than_session_end_nan_d7() -> None:
    w = build_windows(np.array([14500, 14200, 14800]), np.array([1, 1, 2]), 3000, 500)
    session1 = int(w.seg_per_block[:2].sum())
    assert session1 > w.lastn
    assert w.session_reference_windows((1,)).size == session1 - (w.lastn - 1)
    assert np.sum(w.session_end_windows() < session1) == w.lastn


def test_windows_run_across_blocks_and_clip_at_the_end() -> None:
    w = build_windows(np.array([600, 600]), np.array([1, 1]), 1000, 500)
    assert w.stops[0] == 999  # starts in block 0, ends in block 1
    assert w.stops[-1] == 1199  # clipped to the last bin


def test_matlab_round_is_half_away_from_zero() -> None:
    assert matlab_round(2.5) == 3 and round(2.5) == 2
    assert matlab_round(6.0) == 6 and matlab_round(-2.5) == -3


@pytest.mark.parametrize("step", [500, 50])
def test_session_crossing_and_clipped_windows_are_all_nan_later(step: int) -> None:
    """With realistic block lengths, SetIndstoNaN covers every window that leaves its session."""
    lengths = np.array([14500, 14200, 14800, 13900, 14300, 11800, 12000])
    sessions = np.array([1, 1, 2, 2, 3, 4, 4])
    w = build_windows(lengths, sessions, 3000, step)
    session_of_bin = np.repeat(sessions, lengths)
    crossing = np.flatnonzero(session_of_bin[w.stops] != w.session_of_window)
    clipped = np.flatnonzero(w.stops - w.starts + 1 < 3000)
    nan_set = set(w.session_end_windows().tolist())
    assert crossing.size > 0 and set(crossing.tolist()) <= nan_set
    assert set(clipped.tolist()) <= nan_set
