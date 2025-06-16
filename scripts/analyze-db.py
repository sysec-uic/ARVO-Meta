#! /usr/bin/env python3
import sqlite3
import argparse
import subprocess
import os
from collections import defaultdict

# ANSI color codes
GREEN = '\033[92m'
CYAN = '\033[96m'
YELLOW = '\033[93m'
MAGENTA = '\033[95m'
RED = '\033[91m'
RESET = '\033[0m'

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, '..', 'arvo.db')

BUG_QUERY_ALL = "SELECT localId, crash_type, fix_commit FROM arvo WHERE project = ?"

# Query to get all fix commits for a specific project
def query_fix_commits(db_path, project):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(BUG_QUERY_ALL, (project,))
    rows = cursor.fetchall()
    conn.close()
    return rows

# Get patch stats for a specific commit
def get_patch_stats(fix_commit, repo_path):
    try:
        result = subprocess.run(
            ['git', '-C', repo_path, 'show', '--stat', '--oneline', fix_commit],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        output = result.stdout.strip().splitlines()
        changed_files = set()
        total_changed_lines = 0

        for line in output:
            if '|' in line and ('+' in line or '-' in line):
                parts = line.strip().split('|')
                filename = parts[0].strip()
                changed_files.add(filename)
                if len(parts) > 1:
                    summary = parts[1].strip().split()
                    if summary:
                        changes = summary[0]
                        if changes.isdigit():
                            total_changed_lines += int(changes)
        return changed_files, total_changed_lines
    except subprocess.CalledProcessError as e:
        print(f"Error retrieving patch for commit {fix_commit}: {e}")
        return set(), 0

# Categorize patch stats into buckets
def categorize_stats(patch_line_stats, patch_file_stats, show_ids=False):
    buckets = {
        "1 line": [],
        "<5 lines": [],
        "5-10 lines": [],
        "10-20 lines": [],
        ">20 lines": []
    }
    file_buckets = {
        "1 file": [],
        ">1 file": defaultdict(list)
    }

    for patch_id in patch_line_stats:
        # patch_line_stats[patch_id] is a list of (fix_commit, local_id) or (total_changed_lines, local_id)
        for (fix_commit, local_id, total_lines, file_count) in patch_line_stats[patch_id]:
            if total_lines == 1:
                buckets["1 line"].append(local_id)
            elif total_lines < 5:
                buckets["<5 lines"].append(local_id)
            elif total_lines <= 10:
                buckets["5-10 lines"].append(local_id)
            elif total_lines <= 20:
                buckets["10-20 lines"].append(local_id)
            else:
                buckets[">20 lines"].append(local_id)

            if file_count == 1:
                file_buckets["1 file"].append(local_id)
            else:
                file_buckets[">1 file"][file_count].append(local_id)

    print("\nLine Change Statistics:")
    for k, v in buckets.items():
        if k == "1 line":
            color = GREEN
        elif k == "<5 lines":
            color = CYAN
        elif k == "5-10 lines":
            color = YELLOW
        elif k == "10-20 lines":
            color = MAGENTA
        elif k == ">20 lines":
            color = RED
        else:
            color = RESET
        print(f"{color}{k}{RESET}: {len(v)} patches")
        if show_ids and v:
            print(f"  localIds: {sorted(v)}")

    print("\nFile Change Statistics:")
    # 1 file: Cyan, >1 file: Red
    print(f"{CYAN}1 file{RESET}: {len(file_buckets['1 file'])} patches")
    if show_ids and file_buckets['1 file']:
        print(f"  localIds: {sorted(file_buckets['1 file'])}")
    for count, vals in sorted(file_buckets[">1 file"].items()):
        print(f"{RED}{count} files{RESET}: {len(vals)} patches")
        if show_ids and vals:
            print(f"  localIds: {sorted(vals)}")

# Extract the patch stat using fix_commit
def analyze_patch_stats(db_path, project, repo_path, show_ids=False):
    rows = query_fix_commits(db_path, project)
    if not rows:
        print(f"No bugs found for project: {project}")
        return
    #print("Tables found:", [row[0] for row in rows])

    patch_line_stats = defaultdict(list)
    patch_file_stats = defaultdict(set)

    for local_id, _, fix_commit in rows:
        if not fix_commit:
            continue
        changed_files, total_changed_lines = get_patch_stats(fix_commit, repo_path)
        file_count = len(changed_files)
        # Store tuple: (fix_commit, local_id, total_changed_lines, file_count)
        patch_line_stats[fix_commit].append((fix_commit, local_id, total_changed_lines, file_count))
        patch_file_stats[fix_commit] = changed_files

    categorize_stats(patch_line_stats, patch_file_stats, show_ids=show_ids)

def main():
    parser = argparse.ArgumentParser(description="Analyze patch stats from arvo.db for a specific project.")
    parser.add_argument('--project', '-p', type=str, required=True, help='Project name from the database')
    parser.add_argument('--show-ids', '-s', action='store_true', help='Display localId for each patch category')
    parser.add_argument('--repo', '-r', type=str, required=True, help='Path to the project repository')
    args = parser.parse_args()

    analyze_patch_stats(DB_PATH, args.project, args.repo, show_ids=args.show_ids)

if __name__ == "__main__":
    main()
