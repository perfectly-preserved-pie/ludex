# Ludex
Latin "ludus" (game) + dex (index)

[![Build and Publish](https://github.com/perfectly-preserved-pie/ludex/actions/workflows/build_and_push.yml/badge.svg)](https://github.com/perfectly-preserved-pie/ludex/actions/workflows/build_and_push.yml)

I made a Dash AG Grid enemy database for Xenosaga a few years ago and found it really fun to build and actually super useful, so I decided to expand that concept into a more general project that can host tools for multiple games.

## AI Disclaimer
With the exception of most of the Xenosaga Enemy Database, which was built years ago, the rest of the code in this repository was generated with the help of AI. I used Codex.

I do my best to review and test all AI-generated code, but there may be bugs. If you find any, please open an issue or submit a PR.

## What Ludex Includes

Current pages in this repository:

- `Xenosaga`: enemy database with sortable, filterable AG Grid tables for Episodes I, II, and III, plus a row-click modal for full enemy details. Docs: [Xenosaga README](games/xenosaga/readme.md)
- `Clair Obscur: Expedition 33`: skill damage data browser, skill damage calculator, and zone level reference table. Docs: [Expedition 33 calculator README](games/expedition33/calculator/README.md)

## Stack

- `Dash` for routing, layout, and callbacks
- `dash-ag-grid` for interactive data tables
- `dash-bootstrap-components` and `dash-mantine-components` for UI
- `pandas` for data loading and shaping
- `gunicorn` for production serving
- `uv` for dependency management

## Project Layout

```text
.
├── app.py                         # Dash app entrypoint and home page
├── games/                         # Dash pages, grouped by game
│   ├── expedition33/
│   └── xenosaga/
├── assets/                        # CSS, JS, CSVs, SQLite DB, static helpers
├── helpers/                       # Shared utility code
├── pyproject.toml                 # Project metadata and dependencies
└── Dockerfile                     # Container build for deployment
```

`app.py` enables Dash Pages with `pages_folder="games"`, so any module under `games/` that calls `register_page(...)` becomes part of the site automatically.

## Running Locally

### With `uv`

```bash
uv sync
uv run python app.py
```

The development server starts on Dash's default local port.

### With Gunicorn

```bash
uv sync
uv run gunicorn -b 0.0.0.0:8080 --workers=4 --preload app:server
```

## Running With Docker

Build the image:

```bash
docker build -t ludex .
```

Run the container:

```bash
docker run --rm -p 8080:8080 ludex
```

Then open `http://localhost:8080`.

## Adding a New Game Page

1. Create a module under `games/<game_name>/`.
2. Define a `layout`.
3. Register the page with Dash using `register_page(...)` and a game-scoped path such as `/<game_name>/<page_name>`.
4. Restart the app.

Once registered, the home tree in `app.py` will automatically group the page under that game.

## Notes

- The top-level app is intentionally generic so multiple games can live in one project.
- Game URLs are namespaced by game, for example `/exp33/skilldamage`.
- Game-specific documentation lives in [Expedition 33 calculator README](games/expedition33/calculator/README.md) and [Xenosaga README](games/xenosaga/readme.md).
