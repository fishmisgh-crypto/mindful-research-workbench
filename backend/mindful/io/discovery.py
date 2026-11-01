"""Find participants, sessions (`day_<n>`) and blocks (`Block_<nn>`) on disk.

Sessions and blocks are ordered numerically. The upstream MATLAB loader orders
sessions by `dir` (alphabetical, D5) and blocks by file modification time (D6);
both alternative orders are recorded so the difference can be checked.
"""

import re
from dataclasses import dataclass
from pathlib import Path

PARTICIPANTS: tuple[str, ...] = ("T11", "T5")
BLOCK_FILES: tuple[str, ...] = ("data.mat", "task.mat", "info.mat")

_SESSION_RE = re.compile(r"^day_(\d+)$")
_BLOCK_RE = re.compile(r"^Block_(\d+)$")


@dataclass(frozen=True)
class BlockRef:
    participant: str
    day: int
    number: int
    path: Path
    missing_files: tuple[str, ...]

    @property
    def name(self) -> str:
        return self.path.name


@dataclass(frozen=True)
class SessionRef:
    participant: str
    day: int
    index: int  # 1-based position in chronological order
    path: Path
    blocks: tuple[BlockRef, ...]
    block_mtime_order_matches_numeric: bool

    @property
    def name(self) -> str:
        return self.path.name


@dataclass(frozen=True)
class ParticipantRef:
    id: str
    path: Path
    sessions: tuple[SessionRef, ...]
    matlab_dir_order: tuple[str, ...]
    ignored_entries: tuple[str, ...]

    @property
    def chronological_order(self) -> tuple[str, ...]:
        return tuple(s.name for s in self.sessions)

    @property
    def dir_order_matches_chronological(self) -> bool:
        return self.matlab_dir_order == self.chronological_order


def _numbered_dirs(
    parent: Path, pattern: re.Pattern[str]
) -> tuple[list[tuple[int, Path]], list[str]]:
    matched: list[tuple[int, Path]] = []
    ignored: list[str] = []
    for entry in parent.iterdir():
        m = pattern.match(entry.name)
        if entry.is_dir() and m:
            matched.append((int(m.group(1)), entry))
        else:
            ignored.append(entry.name)
    return sorted(matched), sorted(ignored)


def _mtime_order_matches(blocks: list[tuple[int, Path]]) -> bool:
    by_mtime = sorted(
        blocks,
        key=lambda nb: (
            (nb[1] / "data.mat").stat().st_mtime if (nb[1] / "data.mat").exists() else 0.0
        ),
    )
    return [n for n, _ in by_mtime] == [n for n, _ in blocks]


def discover_participant(root: Path, participant: str) -> ParticipantRef:
    """Discover one participant's sessions and blocks under `root/participant`."""
    folder = root / participant
    session_dirs, ignored = _numbered_dirs(folder, _SESSION_RE)
    sessions: list[SessionRef] = []
    for index, (day, session_path) in enumerate(session_dirs, start=1):
        block_dirs, block_ignored = _numbered_dirs(session_path, _BLOCK_RE)
        ignored.extend(f"{session_path.name}/{name}" for name in block_ignored)
        blocks = tuple(
            BlockRef(
                participant=participant,
                day=day,
                number=number,
                path=block_path,
                missing_files=tuple(f for f in BLOCK_FILES if not (block_path / f).is_file()),
            )
            for number, block_path in block_dirs
        )
        sessions.append(
            SessionRef(
                participant=participant,
                day=day,
                index=index,
                path=session_path,
                blocks=blocks,
                block_mtime_order_matches_numeric=_mtime_order_matches(block_dirs),
            )
        )
    return ParticipantRef(
        id=participant,
        path=folder,
        sessions=tuple(sessions),
        matlab_dir_order=tuple(sorted(p.name for _, p in session_dirs)),
        ignored_entries=tuple(ignored),
    )


def discover(root: Path) -> dict[str, ParticipantRef]:
    """Discover every expected participant folder that exists under `root`."""
    return {p: discover_participant(root, p) for p in PARTICIPANTS if (root / p).is_dir()}
