#!/bin/bash

set -e

PIN_VERSION="3.31"
PIN_URL="https://software.intel.com/sites/landingpage/pintool/downloads/pin-external-3.31-98869-gfa6f126a8-gcc-linux.tar.gz"
PIN_TARBALL="pin-${PIN_VERSION}.tar.gz"
PIN_DIR="pin-${PIN_VERSION}"
PIN_TOOL_DIR="${PIN_DIR}/source/tools/MyPinTool"
BBTRACE_CPP="bbtrace.cpp"

# Download and extract PIN
echo -e "\033[1;34m[*]\033[0m Downloading PIN..."
wget -O "$PIN_TARBALL" "$PIN_URL"

echo -e "\033[1;34m[*]\033[0m Extracting..."
mkdir -p "$PIN_DIR"
tar -xzf "$PIN_TARBALL" --strip-components=1 -C "$PIN_DIR"
# mv pin-* "$PIN_DIR"

# Prepare MyPinTool directory
echo -e "\033[1;34m[*]\033[0m Setting up MyPinTool..."
mkdir -p "$PIN_TOOL_DIR"
cp "$BBTRACE_CPP" "$PIN_TOOL_DIR/"

# Build the tool
echo -e "\033[1;34m[*]\033[0m Building bbtrace.so..."
make -C "$PIN_TOOL_DIR" obj-intel64/bbtrace.so TARGET=intel64 TOOL_ROOTS=bbtrace

echo -e "\033[1;32m[+]\033[0m Done. You can run your tool with:"
echo -e "\033[1;32m[+]\033[0m $PIN_DIR/pin -t $PIN_TOOL_DIR/obj-intel64/bbtrace.so -- <your_program>"
