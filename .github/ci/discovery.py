#!/usr/bin/env python3
"""Discover packages and flake inputs for update checks."""

import json
import os
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class MatrixItem:
    type: str
    name: str
    current_version: str


def package_version(name: str) -> str:
    result = subprocess.run(
        ["nix", "eval", "--raw", f".#{name}.version"],
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()


def discover_packages(requested: list[str]) -> list[MatrixItem]:
    packages = requested or sorted(
        path.parent.name for path in Path("packages").glob("*/update.py")
    )
    missing = [
        name for name in packages if not Path(f"packages/{name}/update.py").is_file()
    ]
    if missing:
        raise SystemExit(f"packages without update.py: {', '.join(missing)}")
    return [MatrixItem("package", name, package_version(name)) for name in packages]


def discover_inputs(requested: list[str]) -> list[MatrixItem]:
    nodes = json.loads(Path("flake.lock").read_text())["nodes"]
    inputs = requested or sorted(name for name in nodes if name != "root")
    missing = [name for name in inputs if name not in nodes]
    if missing:
        raise SystemExit(f"unknown flake inputs: {', '.join(missing)}")

    items = []
    for name in inputs:
        locked = nodes[name].get("locked", {})
        revision = str(locked.get("rev", "unknown"))[:8]
        items.append(MatrixItem("flake-input", name, revision))
    return items


def write_output(name: str, value: str) -> None:
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with Path(output).open("a") as stream:
            stream.write(f"{name}={value}\n")
    else:
        print(f"{name}={value}")


def main() -> None:
    packages = os.environ.get("PACKAGES", "").split()
    inputs = os.environ.get("INPUTS", "").split()
    items = [*discover_packages(packages), *discover_inputs(inputs)]
    matrix = json.dumps(
        {"include": [asdict(item) for item in items]}, separators=(",", ":")
    )
    write_output("matrix", matrix)
    write_output("has-updates", str(bool(items)).lower())


if __name__ == "__main__":
    main()
