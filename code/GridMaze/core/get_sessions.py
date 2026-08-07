"""Session lookup and file loading for the goalNav_mFC_ephys dataset.

Barebones API:
    get_maze_sessions  -- filter maze sessions by subject / maze / day / goal subset.
    get_maze_session   -- return one specifically identified maze session.
    MazeSession        -- one session's metadata plus selectively loaded data.
    load               -- load a single processed-data file by path.
"""

# %% Imports
import json
from collections.abc import Sequence
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal, TypeAlias, cast

import numpy as np
import pandas as pd
from GridMaze.maze import representations as mr

# %% Paths and data products

DEFAULT_DATA_ROOT = Path(__file__).resolve().parents[3] / "data"

DataKey = Literal[
    "events_df",
    "trials_df",
    "spike_times",
    "spike_clusters",
    "cluster_metrics",
    "tracking_df",
    "trajectories_df",
    "trial_info_df",
    "lfp_times",
    "lfp_signal",
    "lfp_metrics",
]
DataSelection: TypeAlias = Sequence[DataKey] | Literal["all"]

DATA_STRUCTURE2FILENAME: dict[DataKey, str] = {
    "events_df": "events.htsv",
    "trials_df": "trials.htsv",
    "spike_times": "spikes.times.npy",
    "spike_clusters": "spikes.clusters.npy",
    "cluster_metrics": "clusters.metrics.htsv",
    "tracking_df": "frames.tracking.htsv",
    "trajectories_df": "frames.trajectories.htsv",
    "trial_info_df": "frames.trialInfo.htsv",
    "lfp_times": "lfp.times.npy",
    "lfp_signal": "lfp.signal.npy",
    "lfp_metrics": "lfp.metrics.htsv",
}

# %% Session lookup


@lru_cache
def _load_catalogs(
    data_root: Path,
) -> tuple[dict[str, Any], list[str], dict[str, dict[str, str]]]:
    """Load the small experiment catalogs for one data root on first use."""
    experiment_info_path = data_root / "experiment_info"
    maze_configs = cast(
        dict[str, Any], load(experiment_info_path / "maze_configs.json")
    )
    subject_ids = cast(list[str], load(experiment_info_path / "subject_IDs.json"))
    maze_day2date = cast(
        dict[str, dict[str, str]],
        load(experiment_info_path / "maze_day2date.json"),
    )
    return maze_configs, subject_ids, maze_day2date


def _resolve_data_root(data_root: str | Path) -> Path:
    return Path(data_root).expanduser().resolve()


def _normalise_data_keys(with_data: DataSelection) -> list[DataKey]:
    if with_data == "all":
        return list(DATA_STRUCTURE2FILENAME)
    if isinstance(with_data, str):
        requested = [with_data]
    else:
        requested = list(with_data)
    unknown = [key for key in requested if key not in DATA_STRUCTURE2FILENAME]
    if unknown:
        available = ", ".join(DATA_STRUCTURE2FILENAME)
        raise ValueError(f"Unknown data key(s) {unknown}; available keys: {available}")
    return cast(list[DataKey], requested)


def get_maze_sessions(
    subject_IDs: list[str] | Literal["all"] = "all",
    maze_names: list[str] | Literal["all"] = "all",
    days_on_maze: list[int] | Literal["all", "late"] = "all",
    goal_subsets: list[str] | Literal["all"] = "all",
    with_data: DataSelection = (),
    must_have_data: bool = True,
    verbose: bool = False,
    *,
    data_root: str | Path = DEFAULT_DATA_ROOT,
) -> list["MazeSession"]:
    """Return all maze sessions matching the given filters.

    Data products are loaded only when named by ``with_data``; pass ``"all"``
    explicitly to load every product. The return value is always a list, and an
    empty list means that no sessions matched.
    """
    root = _resolve_data_root(data_root)
    maze_configs, known_subject_ids, maze_day2date = _load_catalogs(root)
    requested_data = _normalise_data_keys(with_data)

    requested_subject_ids = known_subject_ids if subject_IDs == "all" else subject_IDs
    requested_maze_names = list(maze_configs) if maze_names == "all" else maze_names
    requested_goal_subsets = (
        ["all", "subset_1", "subset_2"] if goal_subsets == "all" else goal_subsets
    )
    _check_request_inputs(
        requested_subject_ids,
        requested_maze_names,
        days_on_maze,
        requested_goal_subsets,
        known_subject_ids,
        maze_configs,
    )

    sessions: list[MazeSession] = []
    for subject in requested_subject_ids:
        for maze_name in requested_maze_names:
            all_days = [int(day) for day in maze_day2date[maze_name]]
            if days_on_maze == "all":
                requested_days = all_days
            elif days_on_maze == "late":
                requested_days = all_days[-7:]
            else:
                requested_days = days_on_maze
            for day_on_maze in requested_days:
                session_date = maze_day2date[maze_name].get(str(day_on_maze))
                if session_date is None:
                    continue
                session_name = f"{session_date}.maze"
                try:
                    session = MazeSession(
                        subject,
                        session_name,
                        data_root=root,
                    )
                except FileNotFoundError:
                    continue
                if session.goal_subset not in requested_goal_subsets:
                    continue
                if must_have_data and not session._has_files(requested_data):
                    continue
                session.load_data(requested_data, verbose=verbose)
                sessions.append(session)
    return sessions


def get_maze_session(
    subject_ID: str,
    maze_name: str,
    day_on_maze: int,
    *,
    with_data: DataSelection = (),
    must_have_data: bool = True,
    verbose: bool = False,
    data_root: str | Path = DEFAULT_DATA_ROOT,
) -> "MazeSession":
    """Return one session identified by subject, maze, and day on maze."""
    sessions = get_maze_sessions(
        subject_IDs=[subject_ID],
        maze_names=[maze_name],
        days_on_maze=[day_on_maze],
        with_data=with_data,
        must_have_data=must_have_data,
        verbose=verbose,
        data_root=data_root,
    )
    if not sessions:
        raise FileNotFoundError(
            f"No session found for {subject_ID}, {maze_name}, day {day_on_maze}."
        )
    if len(sessions) > 1:
        raise RuntimeError(
            f"Expected one session for {subject_ID}, {maze_name}, day {day_on_maze}; "
            f"found {len(sessions)}."
        )
    return sessions[0]


def _check_request_inputs(
    subject_ids: list[str],
    maze_names: list[str],
    days_on_maze: list[int] | Literal["all", "late"],
    goal_subsets: list[str],
    known_subject_ids: list[str],
    maze_configs: dict[str, Any],
) -> None:
    """Raise a useful error when a session filter is invalid."""
    if not isinstance(days_on_maze, list) and days_on_maze not in ["all", "late"]:
        raise ValueError(f"{days_on_maze} must be a list, 'all', or 'late'")
    for subject_id in subject_ids:
        if subject_id not in known_subject_ids:
            raise ValueError(f"{subject_id} not in subject_IDs.json")
    for maze_name in maze_names:
        if maze_name not in maze_configs:
            raise ValueError(f"{maze_name} not in maze_configs.json")
    valid_goal_subsets = {"all", "subset_1", "subset_2"}
    unknown_goal_subsets = set(goal_subsets) - valid_goal_subsets
    if unknown_goal_subsets:
        raise ValueError(f"Unknown goal subset(s): {sorted(unknown_goal_subsets)}")


# %% Session class


class MazeSession:
    """One session's explicit metadata plus optionally loaded data products."""

    subject_ID: str
    session_type: str
    session_date: str
    experimental_day: int
    maze_name: str
    maze_structure: list[str]
    day_on_maze: int
    goal_subset: str
    goals: list[str]
    reward_size: str
    probe_depth: float
    tissue_sample: str

    events_df: pd.DataFrame | None
    trials_df: pd.DataFrame | None
    spike_times: np.ndarray | None
    spike_clusters: np.ndarray | None
    cluster_metrics: pd.DataFrame | None
    tracking_df: pd.DataFrame | None
    trajectories_df: pd.DataFrame | None
    trial_info_df: pd.DataFrame | None
    lfp_times: np.ndarray | None
    lfp_signal: np.ndarray | None
    lfp_metrics: pd.DataFrame | None

    def __init__(
        self,
        subject: str,
        session_name: str,
        with_data: DataSelection = (),
        verbose: bool = False,
        *,
        data_root: str | Path = DEFAULT_DATA_ROOT,
    ) -> None:
        self._data_root = _resolve_data_root(data_root)
        self._processed_data_path = (
            self._data_root / "processed_data" / subject / session_name
        )
        session_info = load(self._processed_data_path / "session_info.json")
        if not isinstance(session_info, dict):
            raise TypeError("session_info.json must contain a JSON object")
        self.session_info: dict[str, Any] = session_info
        self.name = f"{subject}.{session_name}"

        self.subject_ID = session_info["subject_ID"]
        self.session_type = session_info["session_type"]
        self.session_date = session_info["session_date"]
        self.experimental_day = session_info["experimental_day"]
        self.maze_name = session_info["maze_name"]
        self.maze_structure = session_info["maze_structure"]
        self.day_on_maze = session_info["day_on_maze"]
        self.goal_subset = session_info["goal_subset"]
        self.goals = session_info["goals"]
        self.reward_size = session_info["reward_size"]
        self.probe_depth = session_info["probe_depth"]
        self.tissue_sample = session_info["tissue_sample"]
        self.date = date.fromisoformat(self.session_date)

        _, _, maze_day2date = _load_catalogs(self._data_root)
        all_days = [int(day) for day in maze_day2date[self.maze_name]]
        self.late_session = self.day_on_maze in all_days[-7:]

        self.events_df = None
        self.trials_df = None
        self.spike_times = None
        self.spike_clusters = None
        self.cluster_metrics = None
        self.tracking_df = None
        self.trajectories_df = None
        self.trial_info_df = None
        self.lfp_times = None
        self.lfp_signal = None
        self.lfp_metrics = None

        self.load_data(with_data, verbose=verbose)

    @property
    def has_data(self) -> list[DataKey]:
        """Names of data products currently loaded on this session."""
        return [
            key for key in DATA_STRUCTURE2FILENAME if getattr(self, key) is not None
        ]

    def _has_files(self, with_data: DataSelection) -> bool:
        """Return whether every requested data product exists on disk."""
        data_keys = _normalise_data_keys(with_data)
        return all(
            (self._processed_data_path / DATA_STRUCTURE2FILENAME[key]).is_file()
            for key in data_keys
        )

    def load_data(self, with_data: DataSelection, verbose: bool = False) -> None:
        """Load selected data products, leaving missing products as ``None``."""
        for attr_name in _normalise_data_keys(with_data):
            file_path = self._processed_data_path / DATA_STRUCTURE2FILENAME[attr_name]
            try:
                data = load(file_path)
            except FileNotFoundError:
                if verbose:
                    print(f"{file_path.name} not found for {self.name}")
                data = None
            setattr(self, attr_name, data)

    def __repr__(self) -> str:
        """Return a nicely formatted string representation of the session."""
        total_width = 50
        return (
            f"\n-MazeSession{'-' * total_width}\n"
            f"  Subject ID     : {self.subject_ID:<{total_width - 26}}\n"
            f"  Maze Name      : {self.maze_name:<{total_width - 26}}\n"
            f"  Day on Maze    : {self.day_on_maze:<{total_width - 26}}\n"
            f"  Goal Subset    : {self.goal_subset:<{total_width - 26}}\n"
            f"  Date           : {self.date.isoformat():<{total_width - 26}}\n"
            f"{'-' * (total_width + 13)}\n"
        )

    def simple_maze(self):
        """Return a networkx graph with towers as nodes and bridges as edges."""
        return mr.simple_maze(self.maze_structure)

    def skeleton_maze(self):
        """Return the maze graph at sub-tower spatial resolution."""
        return mr.skeleton_maze(self.maze_structure)


# %% File loading


def load(
    filepath: str | Path,
) -> dict[str, Any] | list[Any] | pd.DataFrame | np.ndarray:
    """Load JSON, hierarchical TSV, or NumPy data based on its filename."""
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"File {filepath} does not exist")
    name = filepath.name
    if name.endswith(".json"):
        with filepath.open("r") as infile:
            return json.load(infile)
    if name.endswith(".htsv"):
        df = pd.read_csv(filepath, sep="\t")
        if any("." in column for column in df.columns):
            tuples = [tuple(column.split(".")) for column in df.columns]
            number_of_levels = max(len(column) for column in tuples)
            tuples = [
                column + ("",) * (number_of_levels - len(column)) for column in tuples
            ]
            df.columns = pd.MultiIndex.from_tuples(tuples)
        return df
    if name.endswith(".npy"):
        data = np.load(filepath)
        if name == "lfp.signal.npy":
            data = data.astype(np.float32)
        return data
    raise ValueError(f"File {name} not recognised")
