#!/usr/bin/env python3
"""Writes the codex skill-card assets: tooltip-style sprites and the stat-marks font."""

from __future__ import annotations

from pathlib import Path


def build(pack_src: Path) -> list[Path]:
    """Writes every skill-card asset under ``pack_src`` and returns the paths written."""
    return []


if __name__ == "__main__":
    for written in build(Path(__file__).resolve().parents[1] / "src"):
        print(written)
