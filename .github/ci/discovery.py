#!/usr/bin/env python3
"""Discover packages with update scripts."""

import json
import os
import subprocess
from pathlib import Path


def version(name: str) -> str:
    result = subprocess.run(
        ["nix", "eval", "--raw", f".#{name}.version"],
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()


def main() -> None:
    requested = os.environ.get("PACKAGES", "").split()
    packages = requested or sorted(
        path.parent.name for path in Path("packages").glob("*/update.py")
    )
    missing = [
        name for name in packages if not Path(f"packages/{name}/update.py").is_file()
    ]
    if missing:
        raise SystemExit(f"packages without update.py: {', '.join(missing)}")

    matrix = {
        "include": [
            {"package": name, "current_version": version(name)} for name in packages
        ]
    }
    value = json.dumps(matrix, separators=(",", ":"))
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with Path(output).open("a") as stream:
            stream.write(f"matrix={value}\n")
            stream.write(f"has-packages={str(bool(packages)).lower()}\n")
    else:
        print(value)


if __name__ == "__main__":
    main()
