"""Window index over the concatenated selected bins, ported from `MINDFUL.SelectEpoch`.

All indices here are 0-based positions in the concatenation of every block's
selected bins, in session/block order. Upstream (1-based) equivalents are noted.
"""

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from mindful.preprocess.config import matlab_round

IntArray = npt.NDArray[np.int64]


@dataclass(frozen=True)
class WindowIndex:
    starts: IntArray  # first bin of each window
    stops: IntArray  # last bin (inclusive), clipped to the last selected bin overall
    block_of_window: IntArray  # position of the block the window starts in
    session_of_window: IntArray  # 1-based chronological session the window starts in
    seg_per_block: IntArray  # windows starting in each block: floor(n_selected / step)
    block_session: IntArray  # 1-based session of each block
    n_bins: int
    window_bins: int
    step_bins: int

    @property
    def n_windows(self) -> int:
        return int(self.starts.size)

    @property
    def lastn(self) -> int:
        """round(winlen / updateHz), the upstream trimming count."""
        return matlab_round(self.window_bins / self.step_bins)

    def _session_block_span(self, sessions: tuple[int, ...]) -> tuple[int, int]:
        blocks = np.flatnonzero(np.isin(self.block_session, sessions))
        if blocks.size == 0:
            raise ValueError(f"no blocks in sessions {sessions}")
        return int(blocks[0]), int(blocks[-1])

    def session_reference_windows(self, sessions: tuple[int, ...]) -> IntArray:
        """`GetSessionSegmentInds`: the sessions' windows minus the last lastn-1 (D7)."""
        first_block, last_block = self._session_block_span(sessions)
        cs = np.concatenate([[0], np.cumsum(self.seg_per_block)])
        first = int(cs[first_block])
        last = int(cs[last_block + 1]) - self.lastn  # inclusive
        return np.arange(first, last + 1, dtype=np.int64)

    def bins_covered(self, windows: IntArray) -> IntArray:
        """`GetSegmentData`: unique bins covered by the given windows."""
        if windows.size == 0:
            return np.zeros(0, dtype=np.int64)
        covered = np.zeros(self.n_bins, dtype=bool)
        for w in windows:
            covered[self.starts[w] : self.stops[w] + 1] = True
        return np.flatnonzero(covered).astype(np.int64)

    def session_end_windows(self) -> IntArray:
        """`SetIndstoNaN`: the last lastn windows of every session (0-based)."""
        cs = np.cumsum(self.seg_per_block)
        out: list[IntArray] = []
        for session in np.unique(self.block_session):
            last_block = int(np.flatnonzero(self.block_session == session)[-1])
            end = int(cs[last_block])  # number of windows up to and including that block
            out.append(np.arange(end - self.lastn, end, dtype=np.int64))
        return np.concatenate(out) if out else np.zeros(0, dtype=np.int64)


def build_windows(
    block_lengths: IntArray, block_session: IntArray, window_bins: int, step_bins: int
) -> WindowIndex:
    """Window starts every `step_bins` within each block; each runs `window_bins` forward."""
    lengths = np.asarray(block_lengths, dtype=np.int64)
    offsets = np.concatenate([[0], np.cumsum(lengths)[:-1]])
    seg = lengths // step_bins
    starts = np.concatenate(
        [
            off + np.arange(n, dtype=np.int64) * step_bins
            for off, n in zip(offsets, seg, strict=True)
        ]
    ).astype(np.int64)
    n_bins = int(lengths.sum())
    stops = np.minimum(starts + window_bins - 1, n_bins - 1)
    block_of_window = np.repeat(np.arange(lengths.size, dtype=np.int64), seg)
    sessions = np.asarray(block_session, dtype=np.int64)
    return WindowIndex(
        starts=starts,
        stops=stops,
        block_of_window=block_of_window,
        session_of_window=sessions[block_of_window],
        seg_per_block=seg,
        block_session=sessions,
        n_bins=n_bins,
        window_bins=window_bins,
        step_bins=step_bins,
    )
