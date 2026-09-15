#!/usr/bin/env python3
"""Run package updater and report resulting changes."""

import argparse
import os
import subprocess
from pathlib import Path


def run(
    command: list[str], *, capture: bool = False
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=capture, check=True)


def nix_version(package: str) -> str:
    return run(
        ["nix", "eval", "--raw", f".#{package}.version"], capture=True
    ).stdout.strip()


def has_changes() -> bool:
    result = subprocess.run(
        ["git", "diff", "--quiet", "origin/main"],
        text=True,
        check=False,
    )
    return result.returncode != 0


def write_output(name: str, value: str) -> None:
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with Path(output).open("a") as stream:
            stream.write(f"{name}={value}\n")
    else:
        print(f"{name}={value}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package")
    args = parser.parse_args()

    update_script = Path("packages") / args.package / "update.py"
    if not update_script.is_file():
        raise SystemExit(f"package has no update script: {args.package}")

    run([str(update_script)])
    write_output("updated", str(has_changes()).lower())
    write_output("new_version", nix_version(args.package))


if __name__ == "__main__":
    main()
