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
- `gen_bug_prompt.py` — generates LLM-ready prompts from ARVO bug data for patch generation or analysis
- `libxml2/` or other project's repo — the Git repository of the `libxml2` project (should be initialized and contain all commit history)

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

The `analyze-bug.py` script requires the `--repo` or `-r` argument to specify the project repository directory, `--project` or `-p` for the project name.

```bash
./scripts/analyze-bug.py -r ./libxml2 -p libxml2 -id 42531092   # 42531092 is a bug in libxml2
```

This will generate a bug/patch report with `localId` == 42531092 in the ARVO database, using the specified repository path to retrieve the buggy and fixed code.

**4. Analyze other repositories/bugs**

```bash
git clone https://git.ffmpeg.org/ffmpeg.git
./scripts/analyze-db.py -p ffmpeg -r ./ffmpeg -s
./scripts/analyze-bug.py -r ./ffmpeg -p ffmpeg -id 42477749
```

```bash
git clone https://gitlab.gnome.org/GNOME/libxml2.git
./scripts/analyze-db.py -p openssl -r ./openssl -s
./scripts/analyze-bug.py -r ./openssl -p openssl -id 42539799
```

**5. Generate Prompt for a Bug:**

The `gen_bug_prompt.py` script creates LLM prompts from a given bug entry using the ARVO docker instance and project repository.

```bash
./scripts/gen_bug_prompt.py -r ./libxml2 -p libxml2 -id 42531092
```

This will generate a textual prompt representing the bug and its context, useful for automated repair tools.

<!--
**6. Run DynamoRIO inside the ARVO docker instance (TODO: Buggy not work as expected):**

Download and set up `DynamoRIO` under the `scripts/bblogger` folder:
```
cd scripts/bblogger/
wget https://github.com/DynamoRIO/dynamorio/releases/download/release_11.3.0-1/DynamoRIO-Linux-11.3.0.tar.gz
tar xvf DynamoRIO-Linux-11.3.0.tar.gz
mv DynamoRIO-Linux-11.3.0-1 drio-11
make FULL=1
```
After `make FULL=1`, it will generate the `bblogger.so` file for recording code execution at the basic block level.

Let's use a `libxml2` bug (`#42528804`) as an example:
```
docker run -v $(pwd):/tools/bblogger \
  --user $(id -u):$(id -g) \
  --rm -it n132/arvo:42528804-vul \
  bash -c "cd /tools/bblogger && ./drio-11/bin64/drrun -c ./bblogger.so -- /out/xslt /tmp/poc"
```
At this point, a `bbtrace.log` file should be generated under `scripts/bblogger`. This log records each module loaded by the target program and lists the addresses of the executed code blocks.

We can also use the `symbolize_trace.py` script to get the code location of these code blocks:
```
docker run -v $(pwd):/tools/bblogger \
  --user $(id -u):$(id -g) \
  --rm -it n132/arvo:42528804-vul \
  bash -c "cd /tools/bblogger && python3 symbolize_trace.py -b /out/xslt -t ./bbtrace.log -m xslt"
```
-->

**6. Dynamic Trace Program Execution using Intel PIN tools (TODO: Not Finished):**

Set up the PIN and pintool:
```
./setup_pin_bbtrace.sh
```

```
pin-3.31/pin -t pin-3.31/source/tools/MyPinTool/obj-intel64/bbtrace.so -- ./xslt poc
```

```
grep xslt pin_bbtrace.log > xslt_bbtrace.log
nm xslt | awk '$2 == "T" || $2 == "t"' | grep -vE '(_ZN10__|__sanitizer|_Z|fuzzer|ubsan|msan|interceptor|LLVM)' \
    | awk '{print $1, $3}' > functions.txt
```