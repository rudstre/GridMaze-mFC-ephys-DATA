<div align="center">

### Data repository for *Doohan et al., 2026* [electrophysiology experiment]

![Python](https://img.shields.io/badge/python-3.12-blue)
![Platform](https://img.shields.io/badge/platform-linux-lightgrey)
![Status](https://img.shields.io/badge/status-research-orange)
![License](https://img.shields.io/badge/license-BSD--style-green)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.7863716.svg)](https://doi.org/10.5281/zenodo.7863716)

<pre>
●     ●─────●     ●     ●─────●─────●
│     │     │     │     │     │      
●─────●     ●     ●─────●     ●     ●
│           │     │           │     │
●─────●─────●─────●     ●─────●─────●
│           │     │     │     │     │
●     ●─────●    🐭     ●     ●     ●
│           │     │           │      
●─────●     ●     ●─────●─────●─────●
│           │           │     │     │
●     ●─────●─────●     ●     ●     ●
│     │                 │     │     │
●─────●─────●─────●─────●     ●     ●
</pre>

</div>

---

> 🚧 **Work in progress** 🛠️ — dataset and loader code are actively maintained ahead of final publication of the accompanying manuscript. If you hit a problem, please [open a GitHub issue](https://github.com/peterdoohan/GridMaze-mFC-ephys-DATA/issues) and I'll get back to you as soon as I can.

> 🎯 **New here?** This repo is the recommended starting point if you want the **dataset** — loaders, schema docs, and tutorial notebooks aimed at general data exploration. If you want to reproduce the **paper analyses**, head to the companion [`GridMaze-mFC`](https://github.com/peterdoohan/GridMaze-mFC) repo.

---

**This repo contains:**
- 🧠 **Single-unit + LFP recordings** from mouse medial frontal cortex (mFC) during a goal-directed navigation task
- 🐭 **Behaviour & tracking** — task events (pyControl), video-derived behavioural trajectories
- 🗺️ **Experiment info** – including maze configurations, experiment timelines, etc.
- 📓 **Lightweight loader package and example notebooks** for getting started

> 📦 **Where does the actual data live?** The recordings are archived on Zenodo ([10.5281/zenodo.7863716](https://doi.org/10.5281/zenodo.7863716)) as two zips: `data.zip` (~73 GB) and an optional `results.zip` (~31 GB, only useful for paper-analysis reproduction). After cloning, run `bash download_data.sh --no-results --no-lfp` to pull the lean default (~52 GB on disk) into `data/`. See [Downloading data](#-downloading-data) for all options.

---

> 📜 **Companion paper** lives on [biorxiv]() — check out what we know about the data so far. <br>
> 💻 **Code for paper analyses** lives in the companion [`GridMaze-mFC`](https://github.com/peterdoohan/GridMaze-mFC) repo. <br>
> ⚡ **Opto experiment** code, results, and data live in the sibling [`GridMaze-mFC-opto`](https://github.com/peterdoohan/GridMaze-mFC-opto) repo.

---

## 📊 What's in the dataset

| | |
|---|---|
| **Subjects** | 6 (m2, m3, m4, m6, m7, m8) |
| **Sessions per subject** | 35 maze sessions across 3 mazes — `maze_1` (13 days), `maze_2` (11 days), `rooms_maze` (11 days) — naive to expert on each |
| **Probes** | 6-shank 64-channel Cambridge NeuroTech probes in mFC (prelimbic, anterior cingulate) |
| **Behavioural task** | Goal-directed navigation on an elevated 7×7 grid maze |
| **Per session** | spike times + clusters, LFP signal + times, QC'd trajectories, raw bodypart tracking, task trial events |
| **Dataset size** | ~73 GB unzipped (or ~25 GB without LFP & UnitMatch data, recommended) |

---

## 📁 Repository layout

```
goalNav_mFC_ephys/
├── download_data.sh             <- helper to fetch data + results from Zenodo
├── 💻 code/                     <- loader package + tutorial notebooks
│   ├── GridMaze/                    <- minimal loader + maze graph code
│   │   ├── core/get_sessions.py        <- session lookup + MazeSession + load()
│   │   └── maze/representations.py     <- networkx maze builders
│   ├── processed_data_intro.ipynb      <- tour the per-session files
│   ├── maze_intro.ipynb                <- work with the maze graphs
│   ├── example_analysis.ipynb          <- worked end-to-end analysis
│   └── environment.yml                 <- conda env spec
├── 📦 data/                     <- populated by download_data.sh from Zenodo
│   ├── processed_data/              <- subject/session/ in a standardised format
│   └── experiment_info/             <- subject IDs, maze configs, probe depths, etc.
└── 📈 results/                  <- placeholder for your figures + outputs
```

---

## 📥 Downloading data

`data/` is archived on Zenodo ([10.5281/zenodo.7863716](https://doi.org/10.5281/zenodo.7863716), record `20267467`). The record contains two zips:

| File          | Contents                                              | Size    |
|---------------|-------------------------------------------------------|---------|
| `data.zip`    | `processed_data/` + `experiment_info/`                | ~73 GB  |
| `results.zip` | saved analysis outputs from the parent paper          | ~31 GB  |

> 📈 **About `results.zip`:** it contains cached outputs of paper-specific analyses (permutation tests, compute-heavy fits) from the [`GridMaze-mFC`](https://github.com/peterdoohan/GridMaze-mFC) analysis repo. If you're only exploring the dataset you can skip it — pass `--no-results` (and ignore the `results/` folder).

Pick whichever of the three options below suits you.

### Option 1 (recommended) — `download_data.sh`

From repo root:

```bash
# recommended lean default — data only, no LFP (~52 GB on disk)
bash download_data.sh --no-results --no-lfp

# full bundle — both zips, LFP included (~104 GB on disk)
bash download_data.sh

# custom data destination (e.g. fast scratch disk)
bash download_data.sh --no-results --no-lfp --data-dir /scratch/gridmaze/data

# keep zips around after extracting (for re-extraction or local sharing)
bash download_data.sh --no-results --no-lfp --keep-zip

# full flag reference
bash download_data.sh --help
```

**Notes:**
- 🔁 **Resumable.** If the download is interrupted, just re-run the same command — `curl -C -` picks up where it left off.
- 🔐 **Verified.** MD5 checksums are fetched live from Zenodo's API and compared after each download. Pass `--no-verify` to skip.
- 🧰 **Requirements:** `curl`, `unzip`, `python3`, and either `md5sum` (Linux) or `md5` (macOS).
- 🗂️ **Custom paths.** The loader uses `<repo-root>/data` by default. If `--data-dir` points elsewhere, pass that directory as `data_root` when loading sessions; no symlink or source edit is required.

### Option 2 — `curl` one-liner

If you only want `data.zip` and prefer not to use the helper script. From repo root:

```bash
curl -L -o data.zip https://zenodo.org/records/20267467/files/data.zip
unzip data.zip && rm data.zip
```

### Option 3 — Manual browser download

For users on restricted networks or who prefer a UI:

1. Open [`zenodo.org/records/20267467`](https://zenodo.org/records/20267467) in a browser.
2. Download `data.zip` (required) and `results.zip` (optional).
3. Unzip them at the repo root so the layout matches the tree in [Repository layout](#-repository-layout).

---

## ⚙️ Environment installation

The notebooks and loader package depend on a small set of standard scientific-Python libraries (`numpy`, `pandas`, `networkx`, `matplotlib`, `scipy`, `scikit-learn`) plus `jupyterlab` / `ipykernel` to run the tutorials. The pinned set lives in [`code/environment.yml`](code/environment.yml). Managed with [miniconda](https://docs.conda.io/projects/miniconda/):

```bash
conda env create -f code/environment.yml
conda activate GridMaze_mFC_ephys
PYTHONPATH=code pytest -q code/tests
```

Tested on Linux; should also resolve on macOS / Windows.

---

## 🚀 Quick start

```bash
# 1. clone
git clone https://github.com/peterdoohan/GridMaze-mFC-ephys-DATA goalNav_mFC_ephys
cd goalNav_mFC_ephys

# 2. create + activate env
conda env create -f code/environment.yml
conda activate GridMaze_mFC_ephys

# 3. download data (
bash download_data.sh --no-results --no-lfp

# 4. launch tutorials in your favourite IDE
...
```

## 📦 Processed data

One folder per subject. Each subject folder has a `probe.htsv` (per-channel anatomy from the Allen CCF) plus one folder per session, named `YYYY-MM-DD.maze`. Files follow IBL-like naming conventions `object.attribute.filetype`, where files sharing the same `object` share their first dimension (where possible).

```
processed_data/m2/
├── probe.htsv                   <- per-channel Allen region + probe contact geometry (shared across sessions)
└── 2022-06-23.maze/
    ├── session_info.json            <- subject, date, maze name + structure, day on maze, goals, probe depth, …
    ├── trials.htsv                  <- per-trial: goal, error pokes, event times
    ├── events.htsv                  <- all pyControl events (cues, rewards, port pokes)
    ├── spikes.times.npy             <- spike times (s)                      }  same first dim
    ├── spikes.clusters.npy          <- cluster IDs                          }
    ├── clusters.metrics.htsv        <- per-cluster QC + Allen region + probe contact
    ├── lfp.signal.npy               <- (n_channels, n_samples) LFP in µV    }  same first dim
    ├── lfp.times.npy                <- LFP timestamps                       }
    ├── lfp.metrics.htsv             <- per-channel QC + region + sampling rate
    ├── frames.tracking.htsv         <- raw SLEAP/DLC bodypart positions     }  shared row index
    ├── frames.trajectories.htsv     <- QC'd centroid + head_direction       }
    ├── frames.trialInfo.htsv        <- per-frame trial / trial_phase / goal }
    └── UnitMatch/                   <- inputs for matching cells across recordings (opt-in download)
```

**Conventions**
- ⏱️ All times in **seconds from start of behavioural session** (cross-stream alignment is done at preprocessing time).
- 📏 All other quantities in **SI units** where applicable.
- 🧾 Tables are `.htsv` (tab-separated, header row, human-readable). Arrays are `.npy`. Metadata is `.json`.

> 🔗 **UnitMatch.** The `UnitMatch/` folder contains the inputs needed to run [UnitMatch](https://github.com/EnnyvanBeest/UnitMatch) — a tool for tracking cells across multiple recording sessions. **Excluded from `download_data.sh` by default** to keep `data/` lean; pass `--with-unitmatch` if you need it. See the linked repo for the file format and usage.

Full per-field tour: [`code/processed_data_intro.ipynb`](code/processed_data_intro.ipynb). End-to-end worked example: [`code/example_analysis.ipynb`](code/example_analysis.ipynb).

### Loading sessions

Session lookup is metadata-only by default. Name only the data products needed for an analysis; each known product is always a discoverable attribute and is `None` until loaded.

```python
from GridMaze.core.get_sessions import get_maze_session, get_maze_sessions

session = get_maze_session(
    subject_ID="m2",
    maze_name="maze_1",
    day_on_maze=10,
    with_data=["trials_df", "trajectories_df"],
)

# More products can be loaded later.
session.load_data(["trial_info_df"])

# Plural lookup always returns a list, including when zero or one session matches.
sessions = get_maze_sessions(maze_names=["maze_1"], days_on_maze="late")
```

Both functions accept `data_root=Path("/scratch/gridmaze/data")` when the data lives outside this repository. Imports and default paths do not depend on the process working directory.


## 📓 Tutorials

Three short notebooks live in [`code/`](code/) to get you up and running:

- [`maze_intro.ipynb`](code/maze_intro.ipynb) — build and inspect the three `networkx` maze views (`simple_maze`, `extended_simple_maze`, `skeleton_maze`) from `maze_configs.json`.
- [`processed_data_intro.ipynb`](code/processed_data_intro.ipynb) — load a session with `get_maze_session(...)` and tour each per-session file: `trials_df`, `events_df`, spikes, cluster metrics, raw tracking, QC'd trajectories, per-frame trial info, LFP, and `session_info`.
- [`example_analysis.ipynb`](code/example_analysis.ipynb) — worked example: frame-aligned firing rates, per-location summaries, single-cell visualisation, aggregation across sessions, and a low-dimensional spatial basis.


## 📜 Citation

Please cite both the paper and the dataset:

```bibtex
@article{placeholder,
  title  = {Structured and flexible representations in medial-frontal cortex
            support goal-directed navigation},
  author = {Doohan, Peter T. and Jensen, Kristopher and Chen, Yaqing and
            Godinho, Beatriz and Burns, Charles D.G. and Qin, Chongyu (Xiao) and
            Emery, Josie and Cini, Ryan and Walton, Mark E. and
            Behrens, Timothy E.J. and Akam, Thomas E.},
  year   = {2026}
}

@dataset{doohan_2026_dataset,
  title     = {Data and results for: Structured and flexible representations in
               medial-frontal cortex support goal-directed navigation},
  author    = {Doohan, Peter T. and Behrens, Timothy E.J. and Akam, Thomas E.},
  year      = {2026},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.7863716},
  url       = {https://doi.org/10.5281/zenodo.7863716}
}
```
