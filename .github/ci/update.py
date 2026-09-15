#!/usr/bin/env python3
"""Run a package or flake input updater and report resulting changes."""

import argparse
import json
import os
import subprocess
from pathlib import Path


def run(
    command: list[str], *, capture: bool = False, check: bool = True
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=capture, check=check)


def nix_version(package: str) -> str:
    return run(
        ["nix", "eval", "--raw", f".#{package}.version"], capture=True
    ).stdout.strip()


def has_changes() -> bool:
    result = run(["git", "diff", "--quiet", "origin/main"], check=False)
    return result.returncode != 0


def write_output(name: str, value: str) -> None:
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with Path(output).open("a") as stream:
            stream.write(f"{name}={value}\n")
    else:
        print(f"{name}={value}")


def update_package(name: str) -> str:
    update_script = Path("packages") / name / "update.py"
    if not update_script.is_file():
        raise SystemExit(f"package has no update script: {name}")
    run([str(update_script)])
    return nix_version(name)


def update_flake_input(name: str) -> str:
    run(["nix", "flake", "update", name])
    nodes = json.loads(Path("flake.lock").read_text())["nodes"]
    if name not in nodes:
        raise SystemExit(f"unknown flake input: {name}")
    return str(nodes[name].get("locked", {}).get("rev", "unknown"))[:8]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("type", choices=["package", "flake-input"])
    parser.add_argument("name")
    args = parser.parse_args()

    if args.type == "package":
        new_version = update_package(args.name)
    else:
        new_version = update_flake_input(args.name)

    write_output("updated", str(has_changes()).lower())
    write_output("new_version", new_version)


if __name__ == "__main__":
    main()
