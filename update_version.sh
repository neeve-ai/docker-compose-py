#!/usr/bin/env bash
set -euo pipefail

# Usage: ./update_version.sh <VERSION>
# Example: ./update_version.sh 5.4.0

VERSION="${1:-}"
if [[ -z "$VERSION" ]]; then
    echo "Usage: $0 <VERSION>" >&2
    echo "Example: $0 5.4.0" >&2
    exit 1
fi

if ! [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Error: VERSION must be in format X.Y.Z (e.g., 5.4.0)" >&2
    exit 1
fi

RELEASE_BASE="https://github.com/docker/compose/releases/download/v${VERSION}"
CHECKSUMS_URL="${RELEASE_BASE}/checksums.txt"

echo "Downloading checksums from ${CHECKSUMS_URL}..."
CHECKSUMS=$(curl -fsSL "${CHECKSUMS_URL}")

get_sha() {
    # checksums.txt format: "<sha256> *<filename>"
    echo "$CHECKSUMS" | grep " \*${1}$" | awk '{print $1}'
}

SHA_LINUX_X86_64=$(get_sha "docker-compose-linux-x86_64")
SHA_LINUX_AARCH64=$(get_sha "docker-compose-linux-aarch64")
SHA_DARWIN_X86_64=$(get_sha "docker-compose-darwin-x86_64")
SHA_DARWIN_AARCH64=$(get_sha "docker-compose-darwin-aarch64")
SHA_WINDOWS_X86_64=$(get_sha "docker-compose-windows-x86_64.exe")
SHA_WINDOWS_AARCH64=$(get_sha "docker-compose-windows-aarch64.exe")

# Validate all checksums were found
for var in SHA_LINUX_X86_64 SHA_LINUX_AARCH64 \
           SHA_DARWIN_X86_64 SHA_DARWIN_AARCH64 \
           SHA_WINDOWS_X86_64 SHA_WINDOWS_AARCH64; do
    if [[ -z "${!var}" ]]; then
        echo "Error: Could not find checksum for ${var}" >&2
        exit 1
    fi
done

cat > setup.cfg << EOF
[metadata]
name = docker-compose-py
version = ${VERSION}.0
description = Python wrapper around invoking the Docker Compose CLI (https://github.com/docker/compose)
long_description = file: README.md
long_description_content_type = text/markdown
url = https://github.com/neeve-ai/docker-compose-py
author = oss-robin
license = Apache License Version 2.0
license_files = LICENSE
classifiers =
    Programming Language :: Python :: 3
    Programming Language :: Python :: 3 :: Only
    Programming Language :: Python :: Implementation :: CPython
    Programming Language :: Python :: Implementation :: PyPy

[options]
python_requires = >=3.11
setup_requires =
    setuptools-download

[setuptools_download]
download_scripts =
    [docker-compose]
    group = docker-compose-binary
    marker = sys_platform == "linux" and platform_machine == "x86_64"
    url = ${RELEASE_BASE}/docker-compose-linux-x86_64
    sha256 = ${SHA_LINUX_X86_64}
    [docker-compose]
    group = docker-compose-binary
    marker = sys_platform == "linux" and platform_machine == "aarch64"
    url = ${RELEASE_BASE}/docker-compose-linux-aarch64
    sha256 = ${SHA_LINUX_AARCH64}
    [docker-compose]
    group = docker-compose-binary
    marker = sys_platform == "darwin" and platform_machine == "x86_64"
    url = ${RELEASE_BASE}/docker-compose-darwin-x86_64
    sha256 = ${SHA_DARWIN_X86_64}
    [docker-compose]
    group = docker-compose-binary
    marker = sys_platform == "darwin" and platform_machine == "arm64"
    url = ${RELEASE_BASE}/docker-compose-darwin-aarch64
    sha256 = ${SHA_DARWIN_AARCH64}
    [docker-compose.exe]
    group = docker-compose-binary
    marker = sys_platform == "win32" and platform_machine == "AMD64"
    url = ${RELEASE_BASE}/docker-compose-windows-x86_64.exe
    sha256 = ${SHA_WINDOWS_X86_64}
    [docker-compose.exe]
    group = docker-compose-binary
    marker = sys_platform == "win32" and platform_machine == "ARM64"
    url = ${RELEASE_BASE}/docker-compose-windows-aarch64.exe
    sha256 = ${SHA_WINDOWS_AARCH64}
EOF

echo "setup.cfg updated to version ${VERSION}.0"
echo "Updated SHA-256 hashes for 6 platforms."
