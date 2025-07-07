#! /usr/bin/env python3
import subprocess
import re
import argparse

def parse_trace(trace_path, target_module):
    """Extract addresses for the given module from bbtrace.log"""
    trace_addrs = []

    with open(trace_path, "r") as f:
        for line in f:
            match = re.match(rf"<{re.escape(target_module)}> \+ (0x[0-9a-fA-F]+)", line)
            if match:
                offset = match.group(1)
                trace_addrs.append(offset)

    return trace_addrs

def symbolize_addrs(addrs, binary_path):
    """Call llvm-symbolizer on a list of addresses"""
    results = []

    for addr in addrs:
        # llvm-symbolizer accepts absolute addresses
        # Here we assume addr is relative to the binary's base, so it's fine
        try:
            proc = subprocess.run(
                ["llvm-symbolizer", "--obj=" + binary_path, addr],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            out = proc.stdout.strip().splitlines()
            if len(out) >= 2:
                func, location = out[0], out[1]
                results.append((addr, func, location))
        except Exception as e:
            results.append((addr, "??", f"error: {e}"))

    return results

def main():
    parser = argparse.ArgumentParser(description="Symbolize bbtrace.log for a specific binary")
    parser.add_argument("--binary", "-b", required=True, help="Path to the target binary (e.g., /out/xslt)")
    parser.add_argument("--trace", "-t", required=True, help="Path to bbtrace.log")
    parser.add_argument("--module", "-m", default="xslt", help="Module name to filter (default: xslt)")
    args = parser.parse_args()

    addrs = parse_trace(args.trace, args.module)
    if not addrs:
        print(f"No trace addresses found for module <{args.module}> in {args.trace}")
        return

    print(f"Found {len(addrs)} addresses in trace for module <{args.module}>")
    result = symbolize_addrs(addrs, args.binary)

    print("\n=== Symbolized Trace ===")
    for addr, func, loc in result:
        print(f"{addr} → {func} @ {loc}")

if __name__ == "__main__":
    main()