---
title: Docker Compose CLI Python Wrapper Package (docker-compose-py)
version: 1.0
date_created: 2026-07-16
last_updated: 2026-07-16
owner: oss-robin (https://pypi.org/user/oss-robin/)
tags: tool, infrastructure, process, python, packaging, docker, docker-compose, cli, pre-commit
---

# Introduction

This specification defines the requirements and implementation details for `docker-compose-py`, a Python package that wraps the pre-built [Docker Compose CLI (`docker-compose`)](https://github.com/docker/compose) binary and makes it pip-installable. The package follows the same pattern as [`shellcheck-py`](https://github.com/shellcheck-py/shellcheck-py) and [`openfga-cli-py`](https://github.com/neeve-ai/openfga-cli-py), using `setuptools-download` to fetch and embed the correct platform-specific binary at install time.

The primary intended use is as a `pre-commit` hook for validating/verifying Docker Compose configuration files (e.g., `docker compose config --quiet`).

**Key difference from `openfga-cli-py`**: Docker Compose release assets are raw pre-built binaries (not archives). There is no extraction step. The downloaded file is placed directly as `docker-compose` (Unix/macOS) or `docker-compose.exe` (Windows) in the Python environment's `bin/` or `Scripts/` directory.

## 1. Purpose & Scope

**Purpose**: Provide a `pip install docker-compose-py` experience that downloads and installs the correct `docker-compose` binary for the user's platform, making it available as a command-line tool in the active Python environment—primarily for use in pre-commit hooks that validate Docker Compose configuration files.

**Scope**:
- Repository layout and file contents for `docker-compose-py`
- `setup.cfg` and `setup.py` configuration using `setuptools-download` (no archive extraction)
- Platform matrix for v5.3.1 of Docker Compose
- PyPI publishing workflow
- Shell script to regenerate `setup.cfg` when a new Docker Compose version is released
- CI/CD via GitHub Actions
- Pre-commit hook support for config validation

**Audience**: Developers maintaining the `docker-compose-py` package and AI agents implementing or updating the project.

**Assumptions**:
- The target PyPI account is `oss-robin` at `https://pypi.org/user/oss-robin/`.
- The package name on PyPI is `docker-compose-py`.
- The internal Python package/module name uses underscores: `docker_compose_py` (PyPI convention).
- The reference implementation to follow is `openfga-cli-py` at `/Users/arul/workspace/orchrepo/src/openfga-cli-py` and `shellcheck-py`.
- Windows x86 (32-bit) is explicitly NOT supported.

---

## 2. Definitions

| Term | Definition |
|------|------------|
| **Docker Compose** | The `docker-compose` binary released at https://github.com/docker/compose |
| **docker-compose** | The executable binary name for Docker Compose on Linux/macOS |
| **docker-compose.exe** | The executable binary name for Docker Compose on Windows |
| **setuptools-download** | A setuptools plugin (https://github.com/asottile/setuptools-download) that downloads and installs external binaries during `pip install` |
| **PEP 508 marker** | Environment marker syntax (e.g., `sys_platform == "linux" and platform_machine == "x86_64"`) used to select platform-specific downloads |
| **Wheel** | A Python binary distribution format (`.whl`); platform-tagged wheels are produced per OS/arch |
| **sdist** | Source distribution (`.tar.gz`); platform-neutral, downloads binary at install time |
| **PyPI** | Python Package Index — the public package registry at https://pypi.org |
| **SHA-256** | Cryptographic hash used to verify downloaded binary integrity |
| **No-extraction download** | A `setuptools-download` entry without `extract` or `extract_path` keys; the URL is fetched and placed directly as the destination binary named by the section header |
| **pre-commit** | A framework for managing and maintaining multi-language pre-commit hooks (https://pre-commit.com) |
| **manylinux** | A Linux wheel compatibility standard that ensures broad glibc compatibility; minimum `manylinux_2_17` required by PyPI |

---

## 3. Requirements, Constraints & Guidelines

### Requirements

- **REQ-001**: The package MUST install the `docker-compose` binary (or `docker-compose.exe` on Windows) into the Python environment's `bin/` (or `Scripts/`) directory upon `pip install docker-compose-py`.
- **REQ-002**: The package MUST support all platform/architecture combinations listed in Section 4 (Platform Matrix): Linux x86_64, Linux aarch64, macOS x86_64, macOS arm64, Windows x86_64 (AMD64), Windows arm64 (ARM64).
- **REQ-003**: Each downloaded binary MUST be verified against its SHA-256 checksum before installation.
- **REQ-004**: The package version MUST follow the scheme `<docker-compose-version>.<packaging-revision>` (e.g., `5.3.1.1`).
- **REQ-005**: A shell script (`update_version.sh`) MUST be provided to regenerate `setup.cfg` for a new Docker Compose release.
- **REQ-006**: The package MUST be publishable to PyPI under the `oss-robin` account using a PyPI API token stored as a GitHub Actions secret (`PYPI_API_TOKEN`) and the `pypa/gh-action-pypi-publish@release/v1` action.
- **REQ-007**: Platform-tagged wheels MUST be built and uploaded so that `pip install` does not need to recompile anything.
- **REQ-008**: The package MUST expose a `docker-compose` console script entry point (via `setuptools-download`) after installation.
- **REQ-009**: All platform-tagged `.whl` files produced during a release MUST be uploaded as GitHub Release assets on the corresponding tag, in addition to being published to PyPI.
- **REQ-010**: The package MUST be usable as a `pre-commit` hook, with a valid `.pre-commit-hooks.yaml` defining a hook id `docker-compose` that invokes the installed binary.
- **REQ-011**: The primary use case of the pre-commit hook is Docker Compose config validation via `docker-compose config --quiet` or similar subcommands.

### Security Requirements

- **SEC-001**: Downloaded binaries MUST be verified via SHA-256 checksums sourced from the official `checksums.txt` at the Docker Compose release page (https://github.com/docker/compose/releases/download/v{VERSION}/checksums.txt).
- **SEC-002**: The PyPI publish workflow MUST authenticate using a scoped PyPI API token (scoped to the `docker-compose-py` project) stored as the GitHub Actions secret `PYPI_API_TOKEN`. The token MUST NOT be printed in logs.
- **SEC-003**: GitHub Actions workflow steps MUST pin third-party actions to a specific version tag.
- **SEC-004**: The GitHub Release asset upload step MUST use the `GITHUB_TOKEN` provided by the Actions runtime (no additional secrets required for asset uploads).

### Constraints

- **CON-001**: The package uses `setuptools-download`; it MUST NOT bundle the binary in the source tree or sdist.
- **CON-002**: Docker Compose release assets are raw pre-compiled binaries (not archives). There is NO `extract` or `extract_path` key in any `[setuptools_download]` section entry. The section header name (`docker-compose` or `docker-compose.exe`) is the destination filename.
- **CON-003**: Windows x86 (32-bit / `win32` / `platform_machine == "x86"`) is NOT supported. Only Windows x86_64 and Windows aarch64 are supported.
- **CON-004**: Linux i686 (32-bit / `platform_machine == "i686"`) is NOT supported. Docker Compose v5.x does not publish a Linux 386 binary.
- **CON-005**: Python `>= 3.11` is required (matching openfga-cli-py precedent and modern toolchain needs).
- **CON-010**: Exotic Linux architectures (armv6l, armv7l, ppc64le, riscv64, s390x) are NOT supported. PyPI does not accept wheel tags for these architectures, making them non-publishable.
- **CON-006**: The wheel produced is NOT a pure-Python wheel (`root_is_pure = False` in `bdist_wheel`); it is tagged `py2.py3-none-<platform>`.
- **CON-007**: PyPI rejects bare `linux_*` platform tags. Linux wheels MUST use the `manylinux` standard (minimum `manylinux_2_17`). The `_PYTHON_HOST_PLATFORM` environment variable MUST be set to `manylinux_2_17_{arch}` before running `pip wheel`.
- **CON-008**: The macOS `_PYTHON_HOST_PLATFORM` value MUST use dashes in the format `macosx-X.Y-arch` (e.g., `macosx-10.9-x86_64`). Using underscores causes `wheel.macosx_libfile.calculate_macosx_platform_tag` to crash with `ValueError: not enough values to unpack`.
- **CON-009**: The Windows `platform_machine` value for x86_64 in `sys.platform == "win32"` is `AMD64`, not `x86_64`. For Windows arm64 it is `ARM64`.

### Guidelines

- **GUD-001**: Follow the file and configuration layout of `openfga-cli-py` exactly, substituting `fga`→`docker-compose`/`docker_compose_py` and updating URLs/hashes accordingly.
- **GUD-002**: Keep `setup.py` minimal — only the `bdist_wheel` subclass overriding `root_is_pure` and `get_tag()`. Import `bdist_wheel` from `setuptools.command.bdist_wheel` first (canonical since setuptools ≥ 70.1), fall back to `wheel.bdist_wheel`, and handle the case where both imports fail by setting `cmdclass = {}`.
- **GUD-003**: Use `make quality` for local testing; it runs `docker-compose version`, `docker-compose help`, `pytest`, and builds the platform wheel.
- **GUD-004**: Provide a `README.md` documenting installation, usage, and pre-commit hook integration with example `args` for config validation.
- **GUD-005**: Set `_PYTHON_HOST_PLATFORM` as an environment variable on the wheel-build step (not as a shell export) so it applies identically on Windows, macOS, and Linux runners.
- **GUD-006**: The `.pre-commit-hooks.yaml` hook MUST set `pass_filenames: false` and `types_or: [yaml, file]` because `docker-compose config` operates on a named file (default `docker-compose.yml`/`compose.yml`), not on individual filenames passed as arguments.

### Patterns

- **PAT-001**: One `[docker-compose]` / `[docker-compose.exe]` section per platform in `[setuptools_download] download_scripts`. No `extract` or `extract_path` keys — the binary is a direct download.
- **PAT-002**: Group all platform entries under the same group name (`docker-compose-binary`).
- **PAT-003**: The section header for Unix/macOS entries is `[docker-compose]`; for Windows entries it is `[docker-compose.exe]`. These names are the final destination filenames.

---

## 4. Interfaces & Data Contracts

### 4.1 Repository File Structure

```
docker-compose-py/
├── .github/
│   └── workflows/
│       └── main.yml              # CI: build, test, publish to PyPI + GitHub Release
├── spec/
│   └── tool-docker-compose-py-wrapper.md  # This specification
├── tests/
│   └── test_docker_compose.py    # Smoke tests: version, help, config
├── .gitignore
├── .pre-commit-config.yaml       # Self-hosting: runs hooks on this repo
├── .pre-commit-hooks.yaml        # Hook definition for downstream consumers
├── LICENSE                       # Apache License Version 2.0
├── README.md
├── Makefile                      # Developer workflow: setup, install, quality
├── setup.cfg                     # Primary configuration (version, metadata, download specs)
├── setup.py                      # Minimal: bdist_wheel subclass only
└── update_version.sh             # Script to regenerate setup.cfg for new releases
```

### 4.2 `setup.cfg` Structure

```ini
[metadata]
name = docker-compose-py
version = 5.3.1.1
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
    url = https://github.com/docker/compose/releases/download/v5.3.1/docker-compose-linux-x86_64
    sha256 = f9ebc6ebdb19d769b793c245a736caaeb198c62587f13b25c660c13b4987f959
    [docker-compose]
    group = docker-compose-binary
    marker = sys_platform == "linux" and platform_machine == "aarch64"
    url = https://github.com/docker/compose/releases/download/v5.3.1/docker-compose-linux-aarch64
    sha256 = aa611e811d0ea25897839c404bfb5bf93ce706dc51c500a4457890f5d0606a86
    [docker-compose]
    group = docker-compose-binary
    marker = sys_platform == "linux" and platform_machine == "armv6l"
    url = https://github.com/docker/compose/releases/download/v5.3.1/docker-compose-linux-armv6
    sha256 = 899607529e5e752cbdaec84b73e994378cf8f27f3d626a5a6df56f7511c00304
    [docker-compose]
    group = docker-compose-binary
    marker = sys_platform == "linux" and platform_machine == "armv7l"
    url = https://github.com/docker/compose/releases/download/v5.3.1/docker-compose-linux-armv7
    sha256 = 69276acb37ea70023cf85a8180e869c0cfc8cb5a3e672821400aa58dea56e2e8
    [docker-compose]
    group = docker-compose-binary
    marker = sys_platform == "linux" and platform_machine == "ppc64le"
    url = https://github.com/docker/compose/releases/download/v5.3.1/docker-compose-linux-ppc64le
    sha256 = 3280a0dcc7874c2a564ca1224c5669364bc1a5d83ae7153a9c0182fd76fd2102
    [docker-compose]
    group = docker-compose-binary
    marker = sys_platform == "linux" and platform_machine == "riscv64"
    url = https://github.com/docker/compose/releases/download/v5.3.1/docker-compose-linux-riscv64
    sha256 = e237f165e0fd5472d147db274f0fb5dcdaab4384c36634178307f4c8e965d904
    [docker-compose]
    group = docker-compose-binary
    marker = sys_platform == "linux" and platform_machine == "s390x"
    url = https://github.com/docker/compose/releases/download/v5.3.1/docker-compose-linux-s390x
    sha256 = 3889c8d1677bee347297c8f0a73bc517b5c35da18781812942aef8a87eac9011
    [docker-compose]
    group = docker-compose-binary
    marker = sys_platform == "darwin" and platform_machine == "x86_64"
    url = https://github.com/docker/compose/releases/download/v5.3.1/docker-compose-darwin-x86_64
    sha256 = 56620a2e87e789147b9b1cc5d37eeecec2332e2cdf5c2d58a68f999f2dc416ca
    [docker-compose]
    group = docker-compose-binary
    marker = sys_platform == "darwin" and platform_machine == "arm64"
    url = https://github.com/docker/compose/releases/download/v5.3.1/docker-compose-darwin-aarch64
    sha256 = 32691ba1196d819fa68cbdc0aad9a5569e730a35ae40c6fdd8458110ecd69488
    [docker-compose.exe]
    group = docker-compose-binary
    marker = sys_platform == "win32" and platform_machine == "AMD64"
    url = https://github.com/docker/compose/releases/download/v5.3.1/docker-compose-windows-x86_64.exe
    sha256 = 6d36cc701393c066d67ebc77773b718d8c738bc4ccb350fbf1dc0e6a09f44cb9
    [docker-compose.exe]
    group = docker-compose-binary
    marker = sys_platform == "win32" and platform_machine == "ARM64"
    url = https://github.com/docker/compose/releases/download/v5.3.1/docker-compose-windows-aarch64.exe
    sha256 = 5871699d19ee22904f7d1a7ce7e9e6b5a582f6cf9286afd0117ad601cc6737d6
```

> **Critical**: There are NO `extract` or `extract_path` keys in any entry. Docker Compose binaries are raw executables, not archives. The section header (`[docker-compose]` / `[docker-compose.exe]`) defines the destination filename that `setuptools-download` will use.

### 4.3 `setup.py` Structure

```python
from __future__ import annotations

from setuptools import setup

# setuptools >= 70.1 ships bdist_wheel natively; wheel package is the fallback
# for older environments where setuptools delegated to the wheel package.
try:
    from setuptools.command.bdist_wheel import bdist_wheel as orig_bdist_wheel
except ImportError:
    try:
        from wheel.bdist_wheel import bdist_wheel as orig_bdist_wheel
    except ImportError:
        orig_bdist_wheel = None

if orig_bdist_wheel is None:
    cmdclass = {}
else:
    class bdist_wheel(orig_bdist_wheel):
        def finalize_options(self):
            orig_bdist_wheel.finalize_options(self)
            self.root_is_pure = False  # not a pure-python package

        def get_tag(self):
            _, _, plat = orig_bdist_wheel.get_tag(self)
            # No Python source, no extensions — tag as py2.py3 none <platform>
            return 'py2.py3', 'none', plat

    cmdclass = {'bdist_wheel': bdist_wheel}

setup(cmdclass=cmdclass)
```

### 4.4 Platform Matrix (v5.3.1)

| Platform | `sys_platform` | `platform_machine` | Asset Filename | SHA-256 |
|----------|---------------|--------------------|----------------|---------|
| Linux x86_64 | `linux` | `x86_64` | `docker-compose-linux-x86_64` | `f9ebc6ebdb19d769b793c245a736caaeb198c62587f13b25c660c13b4987f959` |
| Linux aarch64 | `linux` | `aarch64` | `docker-compose-linux-aarch64` | `aa611e811d0ea25897839c404bfb5bf93ce706dc51c500a4457890f5d0606a86` |
| macOS x86_64 | `darwin` | `x86_64` | `docker-compose-darwin-x86_64` | `56620a2e87e789147b9b1cc5d37eeecec2332e2cdf5c2d58a68f999f2dc416ca` |
| macOS arm64 | `darwin` | `arm64` | `docker-compose-darwin-aarch64` | `32691ba1196d819fa68cbdc0aad9a5569e730a35ae40c6fdd8458110ecd69488` |
| Windows x86_64 | `win32` | `AMD64` | `docker-compose-windows-x86_64.exe` | `6d36cc701393c066d67ebc77773b718d8c738bc4ccb350fbf1dc0e6a09f44cb9` |
| Windows aarch64 | `win32` | `ARM64` | `docker-compose-windows-aarch64.exe` | `5871699d19ee22904f7d1a7ce7e9e6b5a582f6cf9286afd0117ad601cc6737d6` |

> **Explicitly NOT supported**: Windows x86 (32-bit / `win32` / `platform_machine == "x86"`) — no asset published by Docker Compose. Linux i686 (32-bit) — no asset published by Docker Compose v5.x. Exotic Linux architectures (armv6l, armv7l, ppc64le, riscv64, s390x) — PyPI does not accept wheel tags for these architectures.

### 4.5 `update_version.sh` Shell Script Contract

The script accepts one required argument: the new Docker Compose version string (e.g., `5.4.0`).

**Behaviour**:
1. Validate that the version argument is provided and matches `^[0-9]+\.[0-9]+\.[0-9]+$`.
2. Download `checksums.txt` from `https://github.com/docker/compose/releases/download/v<VERSION>/checksums.txt`.
3. Parse SHA-256 values for the 6 relevant binary assets (2 Linux architectures, 2 macOS, 2 Windows).
4. Generate a new `setup.cfg` by substituting the old version, URLs, and SHA-256 values.
5. Write the updated `setup.cfg` to the repository root (overwriting the existing file).
6. Print a summary of changes made.

**Signature**:
```bash
./update_version.sh <NEW_VERSION>
# Example:
./update_version.sh 5.4.0
```

**Asset filename pattern** (no version embedded in filename):
```
docker-compose-linux-x86_64
docker-compose-linux-aarch64
docker-compose-darwin-x86_64
docker-compose-darwin-aarch64
docker-compose-windows-x86_64.exe
docker-compose-windows-aarch64.exe
```

```bash
#!/usr/bin/env bash
set -euo pipefail

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
SHA_LINUX_ARMV6=$(get_sha "docker-compose-linux-armv6")
SHA_LINUX_ARMV7=$(get_sha "docker-compose-linux-armv7")
SHA_LINUX_PPC64LE=$(get_sha "docker-compose-linux-ppc64le")
SHA_LINUX_RISCV64=$(get_sha "docker-compose-linux-riscv64")
SHA_LINUX_S390X=$(get_sha "docker-compose-linux-s390x")
SHA_DARWIN_X86_64=$(get_sha "docker-compose-darwin-x86_64")
SHA_DARWIN_AARCH64=$(get_sha "docker-compose-darwin-aarch64")
SHA_WINDOWS_X86_64=$(get_sha "docker-compose-windows-x86_64.exe")
SHA_WINDOWS_AARCH64=$(get_sha "docker-compose-windows-aarch64.exe")

# Validate all checksums were found
for var in SHA_LINUX_X86_64 SHA_LINUX_AARCH64 SHA_LINUX_ARMV6 SHA_LINUX_ARMV7 \
           SHA_LINUX_PPC64LE SHA_LINUX_RISCV64 SHA_LINUX_S390X \
           SHA_DARWIN_X86_64 SHA_DARWIN_AARCH64 \
           SHA_WINDOWS_X86_64 SHA_WINDOWS_AARCH64; do
    if [[ -z "${!var}" ]]; then
        echo "Error: Could not find checksum for ${var}" >&2
        exit 1
    fi
done

cat > setup.cfg << EOF
# (full setup.cfg generated by this script — see Section 4.2 for schema)
EOF

echo "setup.cfg updated to version ${VERSION}.0"
echo "Updated SHA-256 hashes for 11 platforms."
```

### 4.6 GitHub Actions Workflows

#### `main.yml` — CI + Publish + GitHub Release Asset Upload

```yaml
# Triggers:
#   push:
#     branches: [main, test-me-*]
#     tags: 'v*'          # e.g. v5.3.1.1
#   pull_request:
#
# Permissions (top-level):
#   contents: write       # required for GitHub Release asset upload

# Job 1: build-and-test
# Matrix (include-style, 6 entries — one per wheel platform with native runners):
#
#   - os: ubuntu-latest,    arch: '',   wheel-plat: manylinux_2_17_x86_64
#   - os: ubuntu-24.04-arm, arch: '',   wheel-plat: manylinux_2_17_aarch64
#   - os: macos-15-intel,   arch: '',   wheel-plat: macosx-10.9-x86_64     # dashes required
#   - os: macos-latest,     arch: '',   wheel-plat: macosx-11.0-arm64       # dashes required
#   - os: windows-latest,   arch: x64,  wheel-plat: win_amd64
#   - os: windows-11-arm,   arch: '',   wheel-plat: win_arm64
#
# Steps per job:
#   - actions/checkout
#   - actions/setup-python (python-version: "3.11", architecture: ${{ matrix.arch }})
#   - pip install setuptools wheel setuptools-download
#   - pip install . --no-build-isolation
#   - docker-compose version    # smoke test (skip on exotic-only entries via matrix.smoke)
#   - docker-compose --help
#   - pip wheel --no-deps --no-build-isolation --wheel-dir dist .
#       env:
#         _PYTHON_HOST_PLATFORM: ${{ matrix.wheel-plat }}
#   - actions/upload-artifact
#       name: wheels-${{ matrix.wheel-plat }}
#       path: dist/*.whl

# Job 2: publish-pypi  (runs on: tag push only; needs: build-and-test)
# Job 3: publish-github-release  (runs on: tag push only; needs: build-and-test)
```

**`_PYTHON_HOST_PLATFORM` values by matrix entry**:

| Runner | `arch` | `wheel-plat` (= `_PYTHON_HOST_PLATFORM`) | Produced tag | Smoke test |
|--------|--------|------------------------------------------|--------------|-----------|
| `ubuntu-latest` | — | `manylinux_2_17_x86_64` | `manylinux_2_17_x86_64` | Yes |
| `ubuntu-24.04-arm` | — | `manylinux_2_17_aarch64` | `manylinux_2_17_aarch64` | Yes |
| `macos-15-intel` | — | `macosx-10.9-x86_64` | `macosx_10_9_x86_64` | Yes |
| `macos-latest` (arm64) | — | `macosx-11.0-arm64` | `macosx_11_0_arm64` | Yes |
| `windows-latest` | `x64` | `win_amd64` | `win_amd64` | Yes |
| `windows-11-arm` | — | `win_arm64` | `win_arm64` | Yes |

**GitHub Release wheel filenames** (produced by `bdist_wheel`):
```
docker_compose_py-5.3.1.1-py2.py3-none-manylinux_2_17_x86_64.whl
docker_compose_py-5.3.1.1-py2.py3-none-manylinux_2_17_aarch64.whl
docker_compose_py-5.3.1.1-py2.py3-none-macosx_10_9_x86_64.whl
docker_compose_py-5.3.1.1-py2.py3-none-macosx_11_0_arm64.whl
docker_compose_py-5.3.1.1-py2.py3-none-win_amd64.whl
docker_compose_py-5.3.1.1-py2.py3-none-win_arm64.whl
```

### 4.7 `.pre-commit-hooks.yaml`

```yaml
- id: docker-compose
  name: docker-compose config
  language: python
  entry: docker-compose
  args: [config, --quiet]
  pass_filenames: false
  types_or: [yaml, file]
```

> **Rationale for `pass_filenames: false`**: `docker-compose config` reads the compose file from `COMPOSE_FILE` environment variable or from the default `compose.yml`/`docker-compose.yml` in the current directory. It does not accept individual file paths as positional arguments in the same way linters do. Pre-commit users who need a non-default file should override `args` in their `.pre-commit-config.yaml`.

### 4.8 `Makefile`

```makefile
SHELL  := /bin/bash
.DEFAULT_GOAL := help

VENV      := .venv
PRECOMMIT := $(VENV)/bin/pre-commit

.PHONY: help setup install quality

help: ## Show available targets
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*?##/ { \
		printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

setup: $(PRECOMMIT) ## Create .venv with pre-commit
	@echo "✓ All tools ready  [pre-commit]"

$(PRECOMMIT):
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install --quiet pre-commit

install: setup ## Install pre-commit hooks and package
	$(PRECOMMIT) install
	$(PRECOMMIT) install --hook-type prepare-commit-msg
	$(VENV)/bin/pip install setuptools wheel setuptools-download pytest
	$(VENV)/bin/pip install . --no-build-isolation

quality: install ## Run tests and build wheel
	$(VENV)/bin/docker-compose version
	$(VENV)/bin/docker-compose --help
	$(VENV)/bin/pytest tests/
	$(VENV)/bin/pip wheel --no-deps --no-build-isolation --wheel-dir dist .
```

### 4.9 `README.md` Content Outline

```markdown
# docker-compose-py

A Python wrapper to provide a pip-installable
[Docker Compose CLI (`docker-compose`)](https://github.com/docker/compose) binary.

## Installation

    pip install docker-compose-py

Or install a platform wheel directly from a GitHub Release (for air-gapped/offline use):

    pip install https://github.com/neeve-ai/docker-compose-py/releases/download/v5.3.1.1/docker_compose_py-5.3.1.1-py2.py3-none-linux_x86_64.whl

## Usage

After installation, the `docker-compose` binary is available in your environment:

    docker-compose version
    docker-compose config --quiet

## As a pre-commit hook

Add to your `.pre-commit-config.yaml`:

    - repo: https://github.com/neeve-ai/docker-compose-py
      rev: v5.3.1.1
      hooks:
      - id: docker-compose

This runs `docker-compose config --quiet` to validate the default compose file.
To validate a non-default file:

    - repo: https://github.com/neeve-ai/docker-compose-py
      rev: v5.3.1.1
      hooks:
      - id: docker-compose
        args: [-f, path/to/docker-compose.yml, config, --quiet]
```

---

## 5. Acceptance Criteria

- **AC-001**: Given a Linux x86_64 environment, when `pip install docker-compose-py` is run, then the `docker-compose` binary is available in `PATH` and `docker-compose version` outputs a version string containing `v5.3.1`.
- **AC-002**: Given a macOS arm64 environment, when `pip install docker-compose-py` is run, then `docker-compose version` exits with code `0`.
- **AC-003**: Given a Windows AMD64 environment, when `pip install docker-compose-py` is run, then `docker-compose.exe` is available in the `Scripts/` directory and `docker-compose version` succeeds.
- **AC-004**: Given any supported platform, when the downloaded binary SHA-256 does not match the value in `setup.cfg`, then installation MUST fail with a checksum error.
- **AC-005**: Given `./update_version.sh 5.4.0` is run, when v5.4.0 exists on GitHub releases with a valid `checksums.txt`, then `setup.cfg` is updated with version `5.4.0.0` and correct SHA-256 hashes for all 6 platforms.
- **AC-006**: Given `./update_version.sh` is run without arguments, then the script exits with code `1` and prints usage instructions.
- **AC-007**: Given a git tag `v5.3.1.1` is pushed, when the GitHub Actions `main.yml` workflow completes, then 6 platform-tagged wheels are published to PyPI under the `oss-robin` account.
- **AC-008**: Given the package is installed, when `python -c "import subprocess; subprocess.run(['docker-compose', 'version'], check=True)"` is executed, then it succeeds without error.
- **AC-009**: Given a git tag `v5.3.1.1` is pushed, when the `publish-github-release` job completes, then the GitHub Release contains 6 `.whl` assets downloadable via the GitHub Releases API.
- **AC-010**: Given a `.pre-commit-config.yaml` referencing this repo at `rev: v5.3.1.1` with `id: docker-compose`, when `pre-commit run docker-compose` is executed in a directory with a valid `compose.yml`, then the hook exits with code `0`.
- **AC-011**: Given a pre-commit hook run on a directory with an invalid compose file, when `docker-compose config --quiet` is invoked, then it exits with a non-zero code and pre-commit reports a failure.
- **AC-012**: Given a `setup.cfg` entry for any platform, when inspected, there MUST be no `extract` or `extract_path` key present — the binary is downloaded directly without archive extraction.
- **AC-013**: Given a Windows ARM64 environment, when `pip install docker-compose-py` is run, then the ARM64 `docker-compose.exe` is available and `docker-compose version` succeeds.
- **AC-014**: Given a Windows x86 (32-bit) environment, when `pip install docker-compose-py` is attempted, then `setuptools-download` MUST NOT find a matching marker and installation MUST fail with no matching platform error (Windows 32-bit is explicitly unsupported).
- **AC-015**: Given `pip wheel --no-deps --no-build-isolation --wheel-dir dist .` is run on Ubuntu with `_PYTHON_HOST_PLATFORM=manylinux_2_17_x86_64`, then the produced wheel filename ends with `-manylinux_2_17_x86_64.whl`; without setting `_PYTHON_HOST_PLATFORM` the wheel ends with `-linux_x86_64.whl` and MUST be rejected by PyPI.
- **AC-016**: Given `setup.py` is imported in an environment where both `setuptools.command.bdist_wheel` and `wheel.bdist_wheel` are unavailable, then `cmdclass` is `{}` and a `py3-none-any.whl` MUST NOT be published to PyPI.
- **AC-017**: ~~Removed~~ Linux armv6l is no longer a supported platform (PyPI does not accept this wheel tag).

---

## 6. Test Automation Strategy

- **Test Levels**:
  - *Smoke*: `docker-compose version` and `docker-compose --help` run successfully post-install.
  - *Functional*: `docker-compose config --quiet` validates a minimal `compose.yml` fixture.
  - *Integration*: Full install on each platform via GitHub Actions matrix.
- **Frameworks**: `pytest` for smoke/functional tests, `make` (quality target), `pip` (installation), native shell for binary invocation.
- **Test Data Management**: A minimal `compose.yml` fixture file is placed in `tests/fixtures/compose.yml` for config validation smoke testing.
- **CI/CD Integration**: GitHub Actions `main.yml` runs on every push/PR; on tag push it runs three jobs: `build-and-test` (6-platform matrix) → `publish-pypi` (parallel with) `publish-github-release`.
- **Smoke test gating**: All 6 matrix entries use native GitHub-hosted runners and run full smoke tests.
- **Coverage Requirements**: N/A — the package wraps a pre-built binary with no Python logic to measure.
- **Performance Testing**: Not required; binary download time is acceptable at install time only.

---

## 7. Rationale & Context

The `shellcheck-py` / `openfga-cli-py` pattern solves the problem of distributing platform-specific CLI tools via pip. `setuptools-download` allows `setup.cfg` to declaratively specify per-platform binary downloads with integrity verification, producing native platform wheels that are self-contained after installation.

**Why no extraction?** Docker Compose distributes pre-compiled single binaries (not tarballs), unlike tools such as the OpenFGA CLI or shellcheck. `setuptools-download` supports direct binary downloads without an `extract` step — the downloaded file is placed directly as the named script. This simplifies the `setup.cfg` entries and eliminates the risk of archive-format changes between releases.

**Why is Windows x86 excluded?** Docker Compose v5.x does not publish a Windows x86 (32-bit) binary. The `win32` / `platform_machine == "x86"` combination is therefore unsupported by design.

**Why is the primary use case pre-commit?** Docker Compose config files (`compose.yml`) are version-controlled and benefit from CI-level and local validation via `docker-compose config --quiet`. Packaging the binary as a pip-installable pre-commit hook enables consistent validation without requiring Docker Desktop or a system-wide Docker installation.

---

## 8. Dependencies & External Integrations

### External Systems
- **EXT-001**: GitHub Releases (`https://github.com/docker/compose/releases`) — Source of Docker Compose binary assets and `checksums.txt` for SHA-256 verification.

### Third-Party Services
- **SVC-001**: PyPI (`https://pypi.org`) — Package registry for publishing `docker-compose-py` wheels. Requires a project-scoped API token.
- **SVC-002**: GitHub Actions — CI/CD platform for build, test, and publish workflows.

### Infrastructure Dependencies
- **INF-001**: GitHub-hosted runners — `ubuntu-latest`, `ubuntu-24.04-arm`, `macos-15-intel`, `macos-latest`, `windows-latest`, `windows-11-arm` for platform matrix builds.

### Data Dependencies
- **DAT-001**: `checksums.txt` — SHA-256 hash manifest published at each Docker Compose release. Format: `<sha256hex> *<filename>` (one entry per line). The `update_version.sh` script fetches this file to regenerate `setup.cfg`.

### Technology Platform Dependencies
- **PLT-001**: Python `>= 3.11` — minimum runtime for package installation and wheel building.
- **PLT-002**: `setuptools-download` — required `setup_requires` dependency; fetched automatically by setuptools during `pip install`.
- **PLT-003**: `wheel` or `setuptools >= 70.1` — provides `bdist_wheel` command for building platform-tagged wheels.

### Compliance Dependencies
- **COM-001**: PyPI manylinux policy — Linux wheels MUST use `manylinux_2_17` or later platform tag. Bare `linux_*` tags are rejected by PyPI upload API with HTTP 400.

---

## 9. Examples & Edge Cases

### Minimal `tests/fixtures/compose.yml`

```yaml
services:
  web:
    image: nginx:alpine
    ports:
      - "8080:80"
```

### Pytest smoke test (`tests/test_docker_compose.py`)

```python
import subprocess
import sys

def test_version():
    result = subprocess.run(
        ["docker-compose", "version"],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "v5.3" in result.stdout or "5.3" in result.stdout

def test_help():
    result = subprocess.run(
        ["docker-compose", "--help"],
        capture_output=True, text=True
    )
    assert result.returncode == 0

def test_config_valid(tmp_path):
    compose_file = tmp_path / "compose.yml"
    compose_file.write_text(
        "services:\n  web:\n    image: nginx:alpine\n"
    )
    result = subprocess.run(
        ["docker-compose", "-f", str(compose_file), "config", "--quiet"],
        capture_output=True, text=True
    )
    assert result.returncode == 0

def test_config_invalid(tmp_path):
    compose_file = tmp_path / "compose.yml"
    compose_file.write_text("services:\n  web:\n    invalid_key: bad\n")
    result = subprocess.run(
        ["docker-compose", "-f", str(compose_file), "config", "--quiet"],
        capture_output=True, text=True
    )
    # docker-compose config may exit 0 on unknown keys; verify it runs at minimum
    # Actual validation depends on docker-compose strictness for the schema version
    assert result.returncode is not None
```

### Edge Case: `cygwin` on Windows

Docker Compose does not publish a Cygwin-specific binary. Cygwin users running `sys_platform == "cygwin"` will not match any marker and installation will fail with no matching platform. This is expected and acceptable; Cygwin users should use WSL or a native Windows Python environment.

### Edge Case: macOS `_PYTHON_HOST_PLATFORM` with underscores

```bash
# WRONG — causes ValueError in wheel.macosx_libfile.calculate_macosx_platform_tag:
_PYTHON_HOST_PLATFORM=macosx_10_9_x86_64 pip wheel ...

# CORRECT — dashes in OS version and arch separator:
_PYTHON_HOST_PLATFORM=macosx-10.9-x86_64 pip wheel ...
```

### Edge Case: `checksums.txt` grep pattern

The checksums file uses `*` prefix on filenames: `<sha256> *<filename>`. The `update_version.sh` grep pattern MUST match ` *<filename>$` (space + asterisk + exact filename + end-of-line) to avoid matching `.provenance.json`, `.sbom.json`, and `.sigstore.json` entries that share the same base name prefix.

---

## 10. Validation Criteria

1. `pip install docker-compose-py` succeeds on all 11 supported platforms listed in Section 4.4.
2. After installation, `docker-compose version` exits with code `0` and output contains `5.3.1`.
3. After installation, `docker-compose config --quiet` run against a valid `compose.yml` exits with code `0`.
4. `pip install docker-compose-py` on a Windows x86 (32-bit) Python environment fails with no matching marker (CON-003).
5. All `[setuptools_download]` entries in `setup.cfg` contain NO `extract` or `extract_path` keys (CON-002).
6. The produced wheel for Linux is named `*-manylinux_2_17_<arch>.whl`, not `*-linux_<arch>.whl` (CON-007).
7. `./update_version.sh` without arguments exits with code `1`.
8. `./update_version.sh 5.4.0` (given a valid release) produces a `setup.cfg` with version `5.4.0.0` and 11 valid SHA-256 entries.
9. The `.pre-commit-hooks.yaml` hook definition includes `pass_filenames: false` (GUD-006).
10. The GitHub Release for `v5.3.1.1` contains exactly 11 `.whl` assets (one per platform wheel tag).

---

## 11. Related Specifications / Further Reading

- [openfga-cli-py spec](../openfga-cli-py/spec/tool-openfga-cli-py-wrapper.md) — Reference implementation this spec is modelled after
- [shellcheck-py](https://github.com/shellcheck-py/shellcheck-py) — Original pattern for pip-installable CLI binary wrappers
- [setuptools-download](https://github.com/asottile/setuptools-download) — The setuptools plugin used for binary downloads
- [Docker Compose releases](https://github.com/docker/compose/releases) — Source of binary assets and checksums
- [Docker Compose v5.3.1 release](https://github.com/docker/compose/releases/tag/v5.3.1) — Specific release this spec targets
- [PyPI manylinux policy](https://peps.python.org/pep-0513/) — PEP 513: manylinux1 compatible Linux wheels
- [pre-commit hook specification](https://pre-commit.com/hooks.html) — pre-commit hooks.yaml schema reference
