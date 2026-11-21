"""Collect page modification dates from tracked content in a Git checkout."""

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPEDITION_ASSETS = "assets/expedition33"
PAGE_SOURCES = {
    "/": ("app.py",),
    "/about": ("app.py", "helpers/seo.py"),
    "/xenosaga": ("games/xenosaga", "assets/xenosaga/xenosaga.db"),
    "/exp33/skilldamage": (
        "games/expedition33/skill_damage.py",
        "games/expedition33/helpers.py",
        f"{EXPEDITION_ASSETS}/clair_skill_damage",
    ),
    "/exp33/calculator": (
        "games/expedition33/calculator_page.py",
        "games/expedition33/calculator",
        "games/expedition33/helpers.py",
        EXPEDITION_ASSETS,
    ),
    "/exp33/zonelevels": (
        "games/expedition33/zonelevels.py",
        f"{EXPEDITION_ASSETS}/zonelevels_mapping.py",
    ),
}


def collect_page_dates() -> dict[str, str]:
    """Find the latest source commit date for each canonical page."""

    dates = {}
    for route, sources in PAGE_SOURCES.items():
        modified = subprocess.check_output(
            ["git", "log", "-1", "--format=%cs", "--", *sources], cwd=ROOT, text=True
        ).strip()
        if modified:
            dates[route] = modified
    return dates


if __name__ == "__main__":
    print(json.dumps(collect_page_dates(), separators=(",", ":")))
