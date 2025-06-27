#! /usr/bin/env python3
import subprocess
import os
import sys
import re
import argparse

# === CONFIGURATION ===
LINES_BEFORE = 10
LINES_AFTER = 10
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CRASH_LOG_FILE = os.path.join(SCRIPT_DIR, "crash_log.txt")
OUTPUT_PROMPT_FILE = os.path.join(SCRIPT_DIR, "llm_bug_prompt.txt")

# A helper function to run shell commands and handle errors
def run_shell(command, cwd=None):
    result = subprocess.run(command, cwd=cwd, shell=True, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if result.returncode != 0 and not result.stdout:
        print(f"[!] Command failed: {command}")
        print(result.stdout)
        sys.exit(1)
    return result.stdout.strip()

# Run arvo inside the container to capture the crash log
def run_arvo_and_get_crash_log():
    print("[*] Running arvo inside container to get crash log...")
    cmd = f'docker run --rm -i {CONTAINER_IMAGE} arvo'
    output = run_shell(cmd)
    print("[+] Crash log captured.")
    return output

# Parse the crash log to extract the function name, file path, and line number
def parse_crash_log(log) -> tuple:
    print("[*] Parsing crash log to extract file and line number...")
    match = re.search(r'#0\s+0x[0-9a-f]+\s+in\s+(\w+)\s+([^\s:]+):(\d+)', log)
    if match:
        function = match.group(1)
        filepath = match.group(2)
        line_number = int(match.group(3))
        bug_match = re.search(r'==\d+==\w+: \w+: ([^:\n]+)', log)
        bug_type = bug_match.group(1) if bug_match else "Unknown"
        print(f"[+] Found crash in function: {function}, file: {filepath}, line: {line_number}")
        print(f"[+] Bug type: {bug_type}")
        return function, filepath, line_number, bug_type
    else:
        print("[!] Could not parse crash log.")
        sys.exit(1)

# Extract the commit hash of the vulnerable commit from the container
def get_vulnerable_commit_hash():
    print("[*] Extracting commit hash from container...")
    cmd = f'docker run --rm -i {CONTAINER_IMAGE} bash -c "git --git-dir={DOCKER_PATH}/.git --work-tree={DOCKER_PATH} log -n1 --format=%H"'
    output = run_shell(cmd)
    print(f"[+] Vulnerable commit: {output}")
    return output

# Checkout the specified commit in the local repository
def checkout_commit(repo_path, commit_hash):
    print(f"[*] Checking out commit {commit_hash}...")
    run_shell(f"git checkout {commit_hash}", cwd=repo_path)

# Find the file containing the crash function in the local repository
def find_crash_function_file(repo_path, function_name):
    print(f"[*] Searching for function '{function_name}'...")
    grep_cmd = f'grep -rl "{function_name}" .'
    output = run_shell(grep_cmd, cwd=repo_path)
    files = output.splitlines()
    if not files:
        print("[!] Function not found in repo.")
        sys.exit(1)
    print(f"[+] Found in: {files[0]}")
    return os.path.join(repo_path, files[0])

# Extract the context around the crash function in the specified file
def extract_code_context(file_path, function_name, before=10, after=10):
    print(f"[*] Extracting context from {file_path}...")
    with open(file_path, 'r') as f:
        lines = f.readlines()

    match_line = None
    for i, line in enumerate(lines):
        if function_name in line:
            match_line = i
            break

    if match_line is None:
        print("[!] Function not found in file.")
        sys.exit(1)

    start = max(0, match_line - before)
    end = min(len(lines), match_line + after + 1)
    context = ''.join(lines[start:end])
    return start + 1, end, context  # lines are 1-indexed

# Write the prompt to a file for LLM input
def write_prompt(commit_hash, crash_function, file_path, start_line, end_line, context, output_path):
    print(f"[*] Writing prompt to {output_path}...")
    prompt = f'''You are an expert in C and the {PROJECT_NAME} codebase.

### Buggy Commit
Commit Hash: {commit_hash}

### Crash Function
{crash_function}

### Code Context
File: {file_path}
Lines: {start_line} to {end_line}

```c
{context}
'''
    with open(output_path, 'w') as f:
        f.write(prompt)

# Parse command line arguments
def parse_args():
    parser = argparse.ArgumentParser(description="Generate bug prompt from ARVO crash")
    parser.add_argument("-id", "--id", required=True, help="Local Bug ID in ARVO (e.g., 42528804)")
    parser.add_argument("-r", "--repo", required=True, help="Path to the host repository")
    parser.add_argument("-d", "--docker-path", required=True, help="Path inside Docker to the source directory (e.g., /src/libxml2)")
    return parser.parse_args()

# Initialize global variables for container image and Docker path
def initialize_paths(args):
    global CONTAINER_IMAGE
    global DOCKER_PATH
    global PROJECT_NAME
    CONTAINER_IMAGE = f"n132/arvo:{args.id}-vul"
    DOCKER_PATH = args.docker_path
    LOCAL_REPO_PATH = os.path.abspath(args.repo)
    PROJECT_NAME = os.path.basename(LOCAL_REPO_PATH)
    return LOCAL_REPO_PATH

# Extract context around the crash line in the specified file
def extract_context(crash_file, crash_line, docker_path, repo_path):
    file_path = os.path.join(repo_path, os.path.relpath(crash_file, docker_path))
    start_line = max(1, crash_line - LINES_BEFORE)
    end_line = crash_line + LINES_AFTER
    with open(file_path, 'r') as f:
        lines = f.readlines()
    context = ''.join(lines[start_line - 1:end_line])
    return file_path, start_line, end_line, context

def main():
    args = parse_args()
    LOCAL_REPO_PATH = initialize_paths(args)

    crash_log = run_arvo_and_get_crash_log()
    with open(CRASH_LOG_FILE, "w") as f:
        f.write(crash_log)
    crash_function, crash_file, crash_line, bug_type = parse_crash_log(crash_log)
    print(f"Crash detected in function: {crash_function} at {crash_file}:{crash_line} (type: {bug_type})")

    commit_hash = get_vulnerable_commit_hash()
    checkout_commit(LOCAL_REPO_PATH, commit_hash)

    file_path, start_line, end_line, context = extract_context(crash_file, crash_line, args.docker_path, LOCAL_REPO_PATH)
    write_prompt(commit_hash, crash_function, file_path, start_line, end_line, context, OUTPUT_PROMPT_FILE)

if __name__ == "__main__":
    main()