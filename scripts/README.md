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

- `analyze-bug.py` — the main analysis script
- `arvo.db` — the SQLite database containing crash and patch info
- `libxml2/` — the Git repository of the libxml2 project (should be initialized and contain all commit history)

## 📌 Usage

```bash
git clone --branch analysis https://github.com/sysec-uic/ARVO-Meta.git; cd ARVO-Meta

git clone https://gitlab.gnome.org/GNOME/libxml2.git
cd scripts
./analyze-bug.py -h
./analyze-bug.py -id 42531092   # 42531092 is a bug in libxml2
```
This will analyze the bug report with `localId` == 42531092 in the ARVO database.