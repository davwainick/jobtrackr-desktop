#!/usr/bin/env python3
"""Build script to create standalone executables for JobTrackr.

Run on each target platform:
    python build.py

Produces:
    dist/JobTrackr          (Linux)
    dist/JobTrackr.exe      (Windows)
    dist/JobTrackr.app      (macOS, with --windowed)
"""

import subprocess
import sys
import platform


def build() -> None:
    system = platform.system()
    print(f"Building JobTrackr for {system}...")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "JobTrackr",
        "--onefile",
        "--clean",
        "--noconfirm",
        # Hidden imports that PyInstaller might miss
        "--hidden-import", "ttkbootstrap",
        "--hidden-import", "ttkbootstrap.themes",
        "--hidden-import", "ttkbootstrap.style",
        "--hidden-import", "ttkbootstrap.widgets",
        "--hidden-import", "ttkbootstrap.constants",
    ]

    # macOS: create a .app bundle with no terminal window
    if system == "Darwin":
        cmd.append("--windowed")

    # Windows: no console window
    if system == "Windows":
        cmd.append("--noconsole")

    # Entry point
    cmd.append("main.py")

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print(f"\nBuild succeeded! Executable is in the dist/ folder.")
        if system == "Windows":
            print("  → dist/JobTrackr.exe")
        elif system == "Darwin":
            print("  → dist/JobTrackr.app")
        else:
            print("  → dist/JobTrackr")
    else:
        print("\nBuild failed.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    build()
