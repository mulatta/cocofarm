#!/usr/bin/env python3
"""Update CocoIndex to the latest stable semantic-versioned release."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_PATH = Path(__file__).with_name("package.nix")
FAKE_HASH = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
SEMVER_RE = re.compile(r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)")
VERSION_RE = re.compile(r'(?m)^(\s*version = ")([^"]+)(";)$')
HASH_RE = re.compile(r'(?m)^(\s*hash = ")([^"]+)(";)$')
GOT_HASH_RE = re.compile(r"got:\s+(sha256-[A-Za-z0-9+/=]+)")


def run(command: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        sys.stderr.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise RuntimeError(f"command failed: {' '.join(command)}")
    return result


def github_release(version: str | None) -> dict[str, Any]:
    suffix = f"tags/v{version}" if version else "latest"
    request = urllib.request.Request(
        f"https://api.github.com/repos/cocoindex-io/cocoindex/releases/{suffix}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "cocofarm-update",
        },
    )
    with urllib.request.urlopen(request) as response:
        data = json.load(response)
    if not isinstance(data, dict):
        raise TypeError("GitHub returned a non-object release")
    return data


def stable_version(release: dict[str, Any]) -> str:
    tag = release.get("tag_name")
    if not isinstance(tag, str) or not tag.startswith("v"):
        raise RuntimeError(f"invalid release tag: {tag!r}")
    version = tag.removeprefix("v")
    if SEMVER_RE.fullmatch(version) is None:
        raise RuntimeError(f"release is not a stable semantic version: {tag!r}")
    if release.get("draft") is not False or release.get("prerelease") is not False:
        raise RuntimeError(f"release is not stable: {tag!r}")
    return version


def package_fields(contents: str) -> tuple[str, list[str]]:
    versions = VERSION_RE.findall(contents)
    hashes = HASH_RE.findall(contents)
    if len(versions) != 1 or len(hashes) != 2:
        raise RuntimeError("package.nix does not have one version and two hashes")
    return versions[0][1], [match[1] for match in hashes]


def replace_version(contents: str, version: str) -> str:
    return VERSION_RE.sub(rf"\g<1>{version}\g<3>", contents, count=1)


def replace_hashes(contents: str, source_hash: str, cargo_hash: str) -> str:
    values = iter((source_hash, cargo_hash))
    return HASH_RE.sub(
        lambda match: f"{match.group(1)}{next(values)}{match.group(3)}", contents
    )


def source_hash(version: str) -> str:
    url = (
        f"https://github.com/cocoindex-io/cocoindex/archive/refs/tags/v{version}.tar.gz"
    )
    result = run(["nix", "store", "prefetch-file", "--json", "--unpack", url])
    data = json.loads(result.stdout)
    value = data.get("hash") if isinstance(data, dict) else None
    if not isinstance(value, str) or not value.startswith("sha256-"):
        raise RuntimeError("nix store prefetch-file returned an invalid hash")
    return value


def cargo_hash() -> str:
    result = run(["nix", "build", "--no-link", ".#cocoindex"], check=False)
    output = result.stdout + result.stderr
    if result.returncode == 0:
        raise RuntimeError("CocoIndex unexpectedly built with the fake cargo hash")
    hashes = GOT_HASH_RE.findall(output)
    if len(hashes) != 1:
        sys.stderr.write(output)
        raise RuntimeError(f"expected one cargo hash mismatch, found {len(hashes)}")
    return hashes[0]


def update(version: str, *, force: bool = False) -> bool:
    original = PACKAGE_PATH.read_text()
    current_version, _hashes = package_fields(original)
    if current_version == version and not force:
        return False

    try:
        new_source_hash = source_hash(version)
        contents = replace_version(original, version)
        PACKAGE_PATH.write_text(replace_hashes(contents, new_source_hash, FAKE_HASH))
        new_cargo_hash = cargo_hash()
        PACKAGE_PATH.write_text(
            replace_hashes(contents, new_source_hash, new_cargo_hash)
        )
    except BaseException:
        PACKAGE_PATH.write_text(original)
        raise
    return PACKAGE_PATH.read_text() != original


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", help="stable release version; defaults to latest")
    parser.add_argument(
        "--force", action="store_true", help="refresh hashes for the current version"
    )
    args = parser.parse_args()

    release = github_release(args.version)
    version = stable_version(release)
    changed = update(version, force=args.force)
    print(f"cocoindex {version}: {'updated' if changed else 'already current'}")


if __name__ == "__main__":
    main()
