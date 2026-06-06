#!/usr/bin/env python3
"""JobTrackr — A standalone job-search CRM application."""

import sys
import os

# Ensure the project root is on sys.path when running from PyInstaller bundle
if getattr(sys, "frozen", False):
    os.chdir(os.path.dirname(sys.executable))
else:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

from ui.app import JobTrackrApp


def main() -> None:
    app = JobTrackrApp()
    app.run()


if __name__ == "__main__":
    main()
