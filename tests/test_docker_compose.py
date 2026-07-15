"""
Tests for docker-compose-py wrapper.

Acceptance Criteria covered:
  AC-001 / AC-002 / AC-003: Binary available after install; `docker-compose version` succeeds.
  AC-008: subprocess invocation works.
  AC-012: setup.cfg contains no `extract` or `extract_path` keys.
  AC-015: Wheel platform tag logic (setup.py bdist_wheel subclass).
  AC-016: setup.py graceful fallback when bdist_wheel is unavailable.
  Functional: config --quiet on valid/invalid compose files.
"""
from __future__ import annotations

import configparser
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent
SETUP_CFG = REPO_ROOT / "setup.cfg"
FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _get_bash() -> str:
    """Return the bash executable path.

    On Windows, ``bash`` in PATH may resolve to the WSL stub
    (``C:\\Windows\\System32\\bash.exe``), which requires WSL distributions
    to be installed and is not available on GitHub Actions runners.  Prefer
    Git for Windows bash, which is always pre-installed on those runners.
    """
    if sys.platform != "win32":
        return "bash"
    git_bash = Path(r"C:\Program Files\Git\bin\bash.exe")
    if git_bash.exists():
        return str(git_bash)
    return "bash"


def run(*args: str, **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(list(args), capture_output=True, text=True, **kwargs)


# ---------------------------------------------------------------------------
# AC-001 / AC-002 / AC-003 / AC-008
# Smoke: binary must be on PATH and respond to `version`
# ---------------------------------------------------------------------------

def test_version():
    """docker-compose version exits 0 and reports v5.3."""
    result = run("docker-compose", "version")
    assert result.returncode == 0, result.stderr
    assert "5.3" in result.stdout or "5.3" in result.stderr


def test_help():
    """docker-compose --help exits 0 (AC-002 / AC-003 smoke)."""
    result = run("docker-compose", "--help")
    assert result.returncode == 0, result.stderr


def test_subprocess_invocation():
    """AC-008: subprocess.run(['docker-compose', 'version'], check=True) must succeed."""
    subprocess.run(["docker-compose", "version"], check=True, capture_output=True)


# ---------------------------------------------------------------------------
# Functional: config validation
# ---------------------------------------------------------------------------

def test_config_valid_fixture():
    """Validate the bundled fixture compose.yml passes config --quiet."""
    compose_file = FIXTURES_DIR / "compose.yml"
    assert compose_file.exists(), f"Missing fixture: {compose_file}"
    result = run("docker-compose", "-f", str(compose_file), "config", "--quiet")
    assert result.returncode == 0, result.stderr


def test_config_valid(tmp_path):
    """A minimal valid compose file passes `config --quiet`."""
    compose_file = tmp_path / "compose.yml"
    compose_file.write_text("services:\n  web:\n    image: nginx:alpine\n")
    result = run("docker-compose", "-f", str(compose_file), "config", "--quiet")
    assert result.returncode == 0, result.stderr


def test_config_invalid(tmp_path):
    """An intentionally broken compose file exits non-zero (AC-011 analogue)."""
    compose_file = tmp_path / "compose.yml"
    # Missing required `image` or `build` key makes compose reject the service.
    compose_file.write_text("services:\n  web: {}\n")
    result = run("docker-compose", "-f", str(compose_file), "config", "--quiet")
    # docker-compose config --quiet exits non-zero for invalid files
    assert result.returncode != 0, (
        "Expected non-zero exit for invalid compose file, but got 0.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


# ---------------------------------------------------------------------------
# AC-012: setup.cfg must have NO extract / extract_path keys
# ---------------------------------------------------------------------------

def test_setup_cfg_no_extract_keys():
    """AC-012: No extract or extract_path keys in any [setuptools_download] entry."""
    content = SETUP_CFG.read_text()
    lines = content.splitlines()
    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        assert not stripped.startswith("extract ="), (
            f"setup.cfg line {i} contains forbidden 'extract' key: {line!r}"
        )
        assert not stripped.startswith("extract_path ="), (
            f"setup.cfg line {i} contains forbidden 'extract_path' key: {line!r}"
        )


# ---------------------------------------------------------------------------
# AC-012 / CON-002: Validate the full platform matrix in setup.cfg
# ---------------------------------------------------------------------------

EXPECTED_PLATFORMS = [
    # (marker snippet, url fragment)
    ('sys_platform == "linux" and platform_machine == "x86_64"',  "docker-compose-linux-x86_64"),
    ('sys_platform == "linux" and platform_machine == "aarch64"', "docker-compose-linux-aarch64"),
    ('sys_platform == "darwin" and platform_machine == "x86_64"', "docker-compose-darwin-x86_64"),
    ('sys_platform == "darwin" and platform_machine == "arm64"',  "docker-compose-darwin-aarch64"),
    ('sys_platform == "win32" and platform_machine == "AMD64"',   "docker-compose-windows-x86_64.exe"),
    ('sys_platform == "win32" and platform_machine == "ARM64"',   "docker-compose-windows-aarch64.exe"),
]


def test_setup_cfg_platform_count():
    """setup.cfg contains entries for exactly 6 platforms."""
    content = SETUP_CFG.read_text()
    marker_count = content.count("marker =")
    assert marker_count == 6, f"Expected 6 platform entries, found {marker_count}"


def test_setup_cfg_all_platforms_present():
    """All 6 expected platform markers and URL fragments exist in setup.cfg."""
    content = SETUP_CFG.read_text()
    for marker, url_fragment in EXPECTED_PLATFORMS:
        assert marker in content, f"Missing marker: {marker}"
        assert url_fragment in content, f"Missing URL fragment: {url_fragment}"


def test_setup_cfg_no_windows_x86():
    """CON-003: Windows x86 (32-bit) must NOT be in setup.cfg."""
    content = SETUP_CFG.read_text()
    assert 'platform_machine == "x86"' not in content, (
        "Windows x86 (32-bit) marker found — CON-003 violation"
    )


def test_setup_cfg_no_linux_i686():
    """CON-004: Linux i686 (32-bit) must NOT be in setup.cfg."""
    content = SETUP_CFG.read_text()
    assert 'platform_machine == "i686"' not in content, (
        "Linux i686 marker found — CON-004 violation"
    )


def test_setup_cfg_version():
    """Package version must be 5.3.1.0 (REQ-004)."""
    content = SETUP_CFG.read_text()
    assert "version = 5.3.1.0" in content


def test_setup_cfg_sha256_present():
    """Each platform entry must have a sha256 key (SEC-001 / REQ-003)."""
    content = SETUP_CFG.read_text()
    sha_count = content.count("sha256 =")
    assert sha_count == 11, f"Expected 11 sha256 entries, found {sha_count}"


# ---------------------------------------------------------------------------
# AC-015 / CON-006: setup.py bdist_wheel subclass
# ---------------------------------------------------------------------------

def test_setup_py_cmdclass():
    """setup.py exposes a bdist_wheel cmdclass that marks root_is_pure = False."""
    import importlib.util, types

    spec_obj = importlib.util.spec_from_file_location(
        "setup_module", REPO_ROOT / "setup.py"
    )
    module = types.ModuleType("setup_module")
    # Patch setup() so it doesn't actually run
    import setuptools
    original_setup = setuptools.setup
    captured = {}

    def mock_setup(**kwargs):
        captured.update(kwargs)

    setuptools.setup = mock_setup
    try:
        loader = spec_obj.loader
        loader.exec_module(module)
    finally:
        setuptools.setup = original_setup

    cmdclass = captured.get("cmdclass", {})
    if not cmdclass:
        # bdist_wheel unavailable in this env — acceptable per AC-016
        pytest.skip("bdist_wheel not available; cmdclass is empty (AC-016 fallback)")

    assert "bdist_wheel" in cmdclass, "cmdclass missing bdist_wheel key"
    bw_cls = cmdclass["bdist_wheel"]

    # Instantiate with a fake dist to inspect root_is_pure
    from distutils.dist import Distribution
    dist = Distribution()
    instance = bw_cls(dist)
    instance.set_undefined_options = lambda *a, **kw: None

    # Call finalize_options via a minimal shim
    try:
        instance.finalize_options()
    except Exception:
        pass  # may fail without full setup context

    assert instance.root_is_pure is False, "root_is_pure should be False (CON-006)"


# ---------------------------------------------------------------------------
# AC-016: graceful fallback when bdist_wheel import fails
# ---------------------------------------------------------------------------

def test_setup_py_fallback_no_bdist_wheel(monkeypatch):
    """AC-016: When bdist_wheel is unavailable, cmdclass must be {} (no crash)."""
    import builtins
    real_import = builtins.__import__

    def patched_import(name, *args, **kwargs):
        if "bdist_wheel" in name:
            raise ImportError(f"Mocked unavailability of {name}")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", patched_import)

    import importlib
    import types as _types

    spec_obj = importlib.util.spec_from_file_location(
        "setup_fallback", REPO_ROOT / "setup.py"
    )
    module = _types.ModuleType("setup_fallback")

    import setuptools
    original_setup = setuptools.setup
    captured = {}

    def mock_setup(**kwargs):
        captured.update(kwargs)

    setuptools.setup = mock_setup
    try:
        spec_obj.loader.exec_module(module)
    finally:
        setuptools.setup = original_setup

    assert captured.get("cmdclass", {}) == {}, (
        "Expected empty cmdclass when bdist_wheel is unavailable (AC-016)"
    )


# ---------------------------------------------------------------------------
# .pre-commit-hooks.yaml validation
# ---------------------------------------------------------------------------

def test_pre_commit_hooks_yaml():
    """GUD-006: .pre-commit-hooks.yaml must have pass_filenames: false."""
    hooks_file = REPO_ROOT / ".pre-commit-hooks.yaml"
    assert hooks_file.exists(), ".pre-commit-hooks.yaml missing"
    content = hooks_file.read_text()
    assert "pass_filenames: false" in content, (
        "GUD-006 violation: pass_filenames: false required"
    )
    assert "id: docker-compose" in content
    assert "entry: docker-compose" in content


# ---------------------------------------------------------------------------
# update_version.sh contract tests (AC-006)
# ---------------------------------------------------------------------------

def test_update_version_no_args():
    """AC-006: update_version.sh without args exits 1 and prints usage."""
    script = REPO_ROOT / "update_version.sh"
    assert script.exists(), "update_version.sh missing"
    result = subprocess.run(
        [_get_bash(), str(script)],
        capture_output=True, text=True
    )
    assert result.returncode == 1
    assert "Usage" in result.stderr or "usage" in result.stderr.lower()


def test_update_version_invalid_format():
    """update_version.sh rejects non-semver version strings."""
    script = REPO_ROOT / "update_version.sh"
    result = subprocess.run(
        [_get_bash(), str(script), "notaversion"],
        capture_output=True, text=True
    )
    assert result.returncode == 1
    assert "Error" in result.stderr or "format" in result.stderr.lower()
