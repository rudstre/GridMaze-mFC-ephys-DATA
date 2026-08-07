import json
import os
import subprocess
import sys
from pathlib import Path
from typing import get_type_hints

import numpy as np
import pandas as pd
import pytest
from GridMaze.core.get_sessions import (
    DATA_STRUCTURE2FILENAME,
    MazeSession,
    get_maze_session,
    get_maze_sessions,
)

SESSION_NAME = "2024-01-01.maze"


@pytest.fixture
def data_root(tmp_path: Path) -> Path:
    experiment_info = tmp_path / "experiment_info"
    session_dir = tmp_path / "processed_data" / "m1" / SESSION_NAME
    experiment_info.mkdir()
    session_dir.mkdir(parents=True)

    catalogs = {
        "maze_configs.json": {"maze_1": {"structure": ["A1-A2"]}},
        "subject_IDs.json": ["m1", "m2"],
        "maze_day2date.json": {"maze_1": {"1": "2024-01-01"}},
    }
    for filename, contents in catalogs.items():
        (experiment_info / filename).write_text(json.dumps(contents))

    session_info = {
        "subject_ID": "m1",
        "session_type": "maze",
        "session_date": "2024-01-01",
        "experimental_day": 3,
        "maze_name": "maze_1",
        "maze_structure": ["A1-A2"],
        "day_on_maze": 1,
        "goal_subset": "all",
        "goals": ["A1", "A2"],
        "reward_size": "8uL",
        "probe_depth": 1400.0,
        "tissue_sample": "C",
        "extra_note": "available only through session_info",
        "simple_maze": "must not replace the method",
    }
    (session_dir / "session_info.json").write_text(json.dumps(session_info))

    table = pd.DataFrame({"value": [1, 2]})
    array = np.array([1.0, 2.0])
    for data_key, filename in DATA_STRUCTURE2FILENAME.items():
        path = session_dir / filename
        if filename.endswith(".htsv"):
            table.to_csv(path, sep="\t", index=False)
        elif data_key == "lfp_signal":
            np.save(path, array.astype(np.float64))
        else:
            np.save(path, array)
    return tmp_path


def test_import_and_graph_construction_do_not_depend_on_cwd(tmp_path: Path) -> None:
    code_root = Path(__file__).resolve().parents[1]
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(code_root)
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from GridMaze.maze.representations import simple_maze; "
                "assert simple_maze(['A1-A2']).has_edge((0, 0), (0, 1))"
            ),
        ],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_metadata_and_data_attributes_are_explicit(data_root: Path) -> None:
    session = MazeSession("m1", SESSION_NAME, data_root=data_root)

    assert session.maze_name == "maze_1"
    assert session.experimental_day == 3
    assert session.session_info["extra_note"] == "available only through session_info"
    assert not hasattr(session, "extra_note")
    assert callable(session.simple_maze)
    assert session.has_data == []
    assert all(getattr(session, key) is None for key in DATA_STRUCTURE2FILENAME)

    type_hints = get_type_hints(MazeSession)
    assert "maze_name" in type_hints
    assert "trial_info_df" in type_hints


def test_load_data_is_repeatable_and_validates_keys(data_root: Path) -> None:
    session = MazeSession("m1", SESSION_NAME, data_root=data_root)

    session.load_data(["trials_df", "spike_times"])
    session.load_data(["trials_df"])

    assert isinstance(session.trials_df, pd.DataFrame)
    assert isinstance(session.spike_times, np.ndarray)
    assert session.has_data == ["trials_df", "spike_times"]
    with pytest.raises(ValueError, match="Unknown data key"):
        session.load_data(["not_a_product"])  # type: ignore[list-item]


def test_missing_data_stays_none_and_can_be_reported(
    data_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    events_path = (
        data_root
        / "processed_data"
        / "m1"
        / SESSION_NAME
        / DATA_STRUCTURE2FILENAME["events_df"]
    )
    events_path.unlink()
    session = MazeSession("m1", SESSION_NAME, data_root=data_root)

    session.load_data(["events_df"], verbose=True)

    assert session.events_df is None
    assert "events.htsv not found" in capsys.readouterr().out


def test_all_loading_loads_every_product(data_root: Path) -> None:
    session = MazeSession("m1", SESSION_NAME, with_data="all", data_root=data_root)

    assert session.has_data == list(DATA_STRUCTURE2FILENAME)
    assert session.lfp_signal is not None
    assert session.lfp_signal.dtype == np.float32


def test_plural_and_singular_lookup_contracts(data_root: Path) -> None:
    sessions = get_maze_sessions(
        subject_IDs=["m1"],
        maze_names=["maze_1"],
        days_on_maze=[1],
        data_root=data_root,
    )

    assert isinstance(sessions, list)
    assert len(sessions) == 1
    assert sessions[0].has_data == []
    assert (
        get_maze_sessions(
            subject_IDs=["m1"],
            maze_names=["maze_1"],
            days_on_maze=[2],
            data_root=data_root,
        )
        == []
    )
    assert (
        get_maze_session("m1", "maze_1", 1, data_root=data_root).name
        == f"m1.{SESSION_NAME}"
    )
    with pytest.raises(FileNotFoundError, match="No session found"):
        get_maze_session("m2", "maze_1", 1, data_root=data_root)


def test_must_have_data_filters_before_loading(data_root: Path) -> None:
    trials_path = (
        data_root
        / "processed_data"
        / "m1"
        / SESSION_NAME
        / DATA_STRUCTURE2FILENAME["trials_df"]
    )
    trials_path.unlink()

    required = get_maze_sessions(
        subject_IDs=["m1"],
        maze_names=["maze_1"],
        days_on_maze=[1],
        with_data=["trials_df"],
        must_have_data=True,
        data_root=data_root,
    )
    optional = get_maze_sessions(
        subject_IDs=["m1"],
        maze_names=["maze_1"],
        days_on_maze=[1],
        with_data=["trials_df"],
        must_have_data=False,
        data_root=data_root,
    )

    assert required == []
    assert len(optional) == 1
    assert optional[0].trials_df is None
