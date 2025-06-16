# Bug and Patch Analyzer for ARVO

This script analyzes crashing inputs and associated fixes for bugs discovered in the [ARVO database](https://github.com/n132/ARVO-Meta).

## 🔍 Features

- Parses crash outputs to extract stack traces.
- Identifies buggy lines in source code from parent (pre-fix) commits.
- Displays surrounding code context for easy review.
- Highlights stack traces and patch diffs with color for readability.
- Supports targeted analysis via `localId` filtering.

## 📁 Prerequisites

- Python 3.6+
- SQLite3
- Git (with `libxml2` repo cloned and accessible)

## 📦 Files Required

- `analyze-db.py` — summarizes all bugs and patches by a specific project using the `fix_commit` from `ARVO.db`
- `analyze-bug.py` — the main analysis script
- `arvo.db` — the SQLite database containing crash and patch info
- `libxml2/` — the Git repository of the libxml2 project (should be initialized and contain all commit history)

## 📌 Usage
**1. Prepare:** Clone only the latest commit of `ARVO-Meta` and then clone `libxml2` under it.

```bash
git clone --depth 1 --branch analysis https://github.com/sysec-uic/ARVO-Meta.git
cd ARVO-Meta
git clone https://gitlab.gnome.org/GNOME/libxml2.git
```

**2. Analyze All Bugs by Project:**
```bash
./scripts/analyze-db.py -h
./scripts/analyze-db.py -p libxml2 -r ./libxml2 -s
```
This summarizes all bugs and patches associated with the `libxml2` project using the repository at `./libxml2`, categorizing them by lines and files changed and optionally displaying `localId`s (using `-s` or `--show-ids`).

**3. Analyze a Specific Bug:**

The `analyze-bug.py` script requires the `--repo` or `-r` argument to specify the project repository directory.

```bash
./scripts/analyze-bug.py -r ./libxml2 -id 42531092   # 42531092 is a bug in libxml2
```
This will analyze the bug report with `localId` == 42531092 in the ARVO database, using the specified repository path to retrieve the faulty and fixed code.
