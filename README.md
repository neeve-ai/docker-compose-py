# docker-compose-py

A Python wrapper to provide a pip-installable
[Docker Compose CLI (`docker-compose`)](https://github.com/docker/compose) binary.

## Installation

```bash
pip install docker-compose-py
```

Or install a platform wheel directly from a GitHub Release (for air-gapped/offline use):

```bash
pip install https://github.com/neeve-ai/docker-compose-py/releases/download/v5.3.1.0/docker_compose_py-5.3.1.0-py2.py3-none-manylinux_2_17_x86_64.whl
```

## Usage

After installation, the `docker-compose` binary is available in your environment:

```bash
docker-compose version
docker-compose config --quiet
```

## As a pre-commit hook

Add to your `.pre-commit-config.yaml`:

```yaml
- repo: https://github.com/neeve-ai/docker-compose-py
  rev: v5.3.1.0
  hooks:
  - id: docker-compose
```

This runs `docker-compose config --quiet` to validate the default compose file
(`compose.yml` or `docker-compose.yml` in the current directory).

To validate a non-default file:

```yaml
- repo: https://github.com/neeve-ai/docker-compose-py
  rev: v5.3.1.0
  hooks:
  - id: docker-compose
    args: [-f, path/to/docker-compose.yml, config, --quiet]
```

## Supported Platforms

| Platform | Architecture |
|----------|-------------|
| Linux | x86_64, aarch64, armv6l, armv7l, ppc64le, riscv64, s390x |
| macOS | x86_64, arm64 |
| Windows | x86_64 (AMD64), arm64 (ARM64) |

> **Note**: Windows x86 (32-bit) and Linux i686 are not supported — Docker Compose v5.x
> does not publish binaries for these architectures.

## Updating to a new Docker Compose version

```bash
./update_version.sh 5.4.0
```

This downloads the `checksums.txt` from the new release and regenerates `setup.cfg`
with updated URLs and SHA-256 hashes for all 11 supported platforms.
