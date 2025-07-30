#! /usr/bin/env python3
import argparse
import sqlite3
import subprocess
import os
import re

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, '..', 'arvo.db')

BUG_QUERY_BY_ID = "SELECT crash_type, crash_output, fix_commit FROM arvo WHERE project = ? AND localId = ?;"

# Extract call stack from crash output
def extract_call_stack(log: str, num_frames: int = 5):
    call_stack_pattern = re.compile(r'^\s*#\d+\s+0x[0-9a-f]+\s+in\s+.*$', re.MULTILINE)
    matches = call_stack_pattern.findall(log)
    return "\n".join(matches[:num_frames])   # Limit to first num_frames lines for brevity

# Parse top stack frame to get file path and line number
def parse_top_stack_frame(stack_trace: str, repo_name: str):
    lines = stack_trace.strip().splitlines()
    if not lines:
        return None, None

    first = lines[0]
    match = re.search(r'in\s+.*?\s+(/src/(.*?):(\d+))', first)
    if match:
        file_path = match.group(2)
        if file_path.startswith(f"{repo_name}/"):
            file_path = file_path[len(repo_name) + 1:]  # Strip repo prefix and slash
        line_number = int(match.group(3))
        return file_path, line_number
    return None, None

# Get file snippet from commit
def get_file_snippet_from_commit(repo_path, commit, file_path, line_number, context=5):
    try:
        content = subprocess.check_output(
            ['git', '-C', repo_path, 'show', f'{commit}:{file_path}'],
            stderr=subprocess.DEVNULL
        ).decode().splitlines()
        start = max(0, line_number - context - 1)
        end = line_number + context
        return "\n".join(content[start:end])
    except subprocess.CalledProcessError:
        return f"⚠️ Could not retrieve {file_path} at {commit}"

# Print colored patch for a commit
def print_colored_patch(repo_path, commit_hash: str):
    # Get the patch for the commit
    patch = subprocess.check_output(['git', '-C', repo_path, 'show', '--format=', commit_hash]).decode()
    print("Files changed in commit:")
    for line in patch.splitlines():
        if line.startswith("diff --git"):
            print(f"\033[96m{line}\033[0m")  # bold cyan
        elif line.startswith("@@"):
            print(f"\033[95m{line}\033[0m")  # bold magenta
        elif line.startswith("+") and not line.startswith("+++"):
            print(f"\033[92m{line}\033[0m")  # green
        elif line.startswith("-") and not line.startswith("---"):
            print(f"\033[91m{line}\033[0m")  # red
        else:
            print(f"\033[90m{line}\033[0m")  # dim white

# Analyze crashes reading from the database
def analyze_crashes(repo_path, target_rows=None, vuln_commit=None, num_frames=5):
    for idx, (crash_type, crash_output, fix_commit) in enumerate(target_rows):
        print(f"\033[94mCrash Type:\033[0m {crash_type}\n")  # Blue label
        
        print("=== Call Stack ===")
        stack_trace = extract_call_stack(crash_output, num_frames)
        print(stack_trace)
        
        print("\nFix Commit:", fix_commit)
        if not fix_commit:
            print("❌ No fix_commit available\n" + "-" * 80)
            continue
        # Get parent commit (i.e., buggy version)
        if vuln_commit:
            parent_commit = vuln_commit
            print("Using provided vulnerable commit:", parent_commit)
        else:
            try:
                parent_commit = subprocess.check_output(['git', '-C', repo_path, 'rev-parse', f'{fix_commit}^']).decode().strip()
                print("Parent Commit:", parent_commit)
            except subprocess.CalledProcessError:
                print("⚠️ Could not find parent commit.\n" + "-" * 80)
                continue

        # Extract file and line number from call stack
        file, line = parse_top_stack_frame(stack_trace, os.path.basename(repo_path.rstrip('/')))
        if file:
            snippet_lines = get_file_snippet_from_commit(repo_path, parent_commit, file, line).splitlines()
            start_line = line - len(snippet_lines) // 2

            print(f"📍 Code near {file}:{line} at {parent_commit[:8]}:")
            for i, code_line in enumerate(snippet_lines):
                current_line = start_line + i
                if current_line == line:
                    print(f"\033[93m👉{code_line}\033[0m")  # yellow
                else:
                    print(f"\033[90m  {code_line}\033[0m")  # dim white

        # Print colored patch for the fix commit
        print_colored_patch(repo_path, fix_commit)
        
        print("-" * 80)


def main():
    parser = argparse.ArgumentParser(description="Analyze a specific crash by localId and project.")
    parser.add_argument('--id', '-id', type=int, required=True, help='Local bug ID from the database')
    parser.add_argument('--repo', '-r', type=str, required=True, help='Path to the project repository')
    parser.add_argument('--project', '-p', type=str, required=True, help='Project name in the database')
    parser.add_argument('--vuln', '-v', type=str, default=None, help='Explicit buggy commit hash (optional)')
    parser.add_argument('--num-frames', '-n', type=int, default=5, help='Number of call stack frames to show (default: 5)')
    args = parser.parse_args()

    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if args.id is not None:
        cursor.execute(BUG_QUERY_BY_ID, (args.project, args.id))
        target_rows = cursor.fetchall()
        if not target_rows:
            print(f"No bug found with localId {args.id}")
            return

    # Analyze the specified crash or all crashes
    analyze_crashes(args.repo, target_rows, vuln_commit=args.vuln, num_frames=args.num_frames)
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
