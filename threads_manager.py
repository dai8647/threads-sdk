#!/usr/bin/env python3
"""Threads Auto-Poster Manager - Interactive Configuration & Posting Tool."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from threads_sdk.autoposter.configurator import Configurator

if __name__ == "__main__":
    configurator = Configurator()
    configurator.run()
