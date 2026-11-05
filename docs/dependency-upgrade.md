# Dependency upgrade review

Reviewed November 5, 2026 against PyPI and upstream release notes.

## Versions

| Direct dependency | Previous pin | Current pin |
| --- | --- | --- |
| Dash | 4.4.1 | 4.5.0, with the compression extra |
| Dash Mantine Components | 2.8.1 | 3.0.0 |
| pandas | 3.1.0 | 3.1.1 |
| Dash AG Grid | 35.3.0 | 35.3.0 (latest stable) |
| Dash Bootstrap Components | 2.0.4 | 2.0.4 (latest stable) |
| Dash Iconify | 0.1.2 | 0.1.2 (latest stable) |
| Gunicorn | 26.2.0 | 26.2.0 (latest stable) |
| Loguru | 0.7.3 | 0.7.3 (latest stable) |
| orjson | Not installed | 3.13.0 |

`uv lock --upgrade` refreshed transitive dependencies as well: 22 existing
packages changed version, including Plotly 7.1.0, NumPy 2.5.4, Werkzeug 3.1.9,
and urllib3 2.8.0. New packages include compression support and the development
test/audit tools. Production dependencies passed `pip-audit` with no known
vulnerabilities at review time. This audit covers Python advisories, not a
complete audit of embedded JavaScript or the container base images.

GitHub Actions were updated to current stable releases with full commit pins.
Dependabot now checks those actions weekly alongside the Python dependencies.

## Dash 4.5 findings

The [Dash 4.5 changelog](https://github.com/plotly/dash/blob/v4.5.0/CHANGELOG.md)
includes fixes that help this app without changing its callback architecture:

- Callback-returned children now reconcile in place. This fixes unnecessary
  remounts and state resets introduced in 4.2, relevant to calculator results
  and navigation. Renderer layout traversal and pattern matching also improved;
  upstream benchmark numbers are not measurements of Ludex.
- Bootstrap tab initialization and callbacks on removed components received
  fixes, relevant to the tabbed grids and multi-page navigation.
- Initial server setup is synchronized, fixing races that could serve 500s for
  component bundles with threaded workers. The current container uses preloaded
  synchronous Gunicorn workers, but the fix also helps future worker changes.
- Additional URL-bearing components block `javascript:` URLs, and page-template
  matching handles problematic paths more safely. Background-callback cache
  isolation and alternate-backend request hooks also received security fixes;
  this app currently uses neither of those features.

Mantine 3 requires React 19. The app explicitly selects React 19.2.4, following
the [Mantine migration guide](https://www.dash-mantine-components.com/migration).
React 19 is opt-in in Dash 4.5. Chromium integration tests exercise the tree,
theme toggle, all character/episode tabs, grids, calculator inputs, and upload
error handling with this combination.

## Improvements implemented

- **Response compression:** `dash[compress]` and `compress=True` compress HTML,
  JSON, and eligible component responses when the browser requests a supported
  encoding. Compression requires no client changes.
- **JSON serialization:** Dash automatically uses the installed `orjson` package.
  This is the supported optimization described in [Dash's performance guide](https://dash.plotly.com/performance).
- **Small detail-click requests:** Both tabbed grids use `getRowId`. Detail
  callbacks look up the original server row by its ID, avoiding a round trip of
  the whole `virtualRowData` table and avoiding reliance on client-supplied row
  contents. Row IDs remain correct after filtering, sorting, or pagination.
- **Explicit skill column types:** Each character sheet supplies its own cell
  types. This fixes mixed text/number columns displaying `Invalid Number` after
  switching from a character whose corresponding column was numeric. Monoco and
  Verso's text-form `Damage Multi` values are also converted to numbers, with
  `-` placeholders kept empty.
- **Request size limit:** Flask rejects request bodies over 16 MiB before JSON
  parsing. This accommodates the existing 10 MiB save limit after base64
  expansion. Save decoding retains its own limit and converter timeout.
- **Regression checks:** Unit, HTTP callback, and Chromium tests run in CI before
  the image build. The production environment excludes development tools.

Local gzip measurements using Flask's test client, with the upgraded app:

| Response | Uncompressed bytes | Gzip bytes | Reduction |
| --- | ---: | ---: | ---: |
| `/xenosaga` initial HTML | 139,911 | 19,789 | 85.9% |
| `/_dash-layout` | 1,664 | 488 | 70.7% |
| `/_dash-dependencies` | 15,026 | 1,690 | 88.8% |

HTML includes a fresh signed token, so compressed byte counts vary slightly.
These are response-size measurements, not end-to-end page-load benchmarks;
production proxies may already compress some responses.

A local serialization microbenchmark of all enemy and skill tab payloads,
using `plotly.io.json.to_json_plotly`, measured 1.924 ms with the `json` engine
and 0.684 ms with `orjson` (best of five batches of 30 serializations).
This isolates serialization, not complete callback latency.

Before the row-ID change, each modal callback sent the visible table back to
the server. The full Episode II rows alone serialize to about 85.7 kB; the new
browser tests verify skill detail requests stay below 2 kB and contain no table
state.

## Dash AG Grid findings and further options

The [upstream release list](https://github.com/plotly/dash-ag-grid/releases)
still identifies 35.3.0 as the latest stable release; 36.0.0rc0 is a preview.
The repository already pinned 35.3.0, so no stable grid package bump was needed.
The pre-existing local virtual environment was older and has now been synced.

Version 35.3 includes fixes for empty row counts, `getRowId=None`, initialization
with sorting, and function parsing. The existing 35.x behavior also provides a
`No Matching Rows` overlay, now covered by a browser test. The app already uses
the modern theme API. See the [migration guide](https://dash.plotly.com/dash-ag-grid/migration-guide).

The new integrated chart and dynamic master/detail features do not currently
replace a slow path here. Adding charts would add interface and bundle costs
without an identified need. Keeping the existing detail dialogs is appropriate.

The most promising larger loading optimization is to replace Enterprise set
filters with community filters, allowing `enableEnterpriseModules=False` and
avoiding the Enterprise JavaScript bundle. That changes the filter UI, so the
current set-filter behavior is retained. Similarly, restoring column
virtualization could reduce DOM work on wide tables, but the current setting
supports sizing every column to its contents; any change needs a deliberate
autosizing strategy and horizontal-scroll checks.

Dash 4.5 callback **request** compression (`compress_payload=True`) is available
for future large state payloads. Removing redundant table state is already a
more direct improvement for the detail callbacks. Streaming callbacks, shared
storage, and WebSockets would add services or worker requirements without
helping the current static grids and short calculations. If those features are
added later, configure shared storage and a common `DASH_SECRET_KEY` across
workers/pods. The current deployment keeps `--preload`.

## Reproducing validation

```bash
uv sync --frozen
uv run --frozen playwright install --with-deps chromium
uv run --frozen pytest -q --run-browser
uv export --frozen --no-dev --no-emit-project --format requirements-txt --output-file /tmp/ludex-requirements.txt > /dev/null
uv run --frozen pip-audit --disable-pip --require-hashes -r /tmp/ludex-requirements.txt
```

Docker cannot be built in the current workspace because Docker Desktop's WSL
integration is unavailable. A separate production-only virtual environment and
Gunicorn with two preloaded workers were used to check the runtime setup.
