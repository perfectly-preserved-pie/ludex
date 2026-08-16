from __future__ import annotations

import re
from html import escape as html_escape
from typing import Any
from xml.sax.saxutils import escape as xml_escape

import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import Input, Output, callback, dcc, html, page_registry, register_page
from dash_iconify import DashIconify
from flask import Response, has_request_context, redirect, request
from games.xenosaga.seo import (
    SITE_ORIGIN,
    XENOSAGA_DESCRIPTION,
    XENOSAGA_PATH,
    XENOSAGA_TITLE,
    build_xenosaga_head_metadata,
    build_xenosaga_static_html,
)


LEGACY_DASH_CHUNK_PATH = re.compile(
    r"^/_dash-component-suites/dash/dcc/\d+\.(async-[A-Za-z0-9_-]+\.js(?:\.map)?)$"
)


class LudexDash(dash.Dash):
    """Dash application with crawlable first-response content for key pages."""

    def interpolate_index(self, **kwargs: str) -> str:
        """Add page-specific server HTML before Dash hydrates the application."""

        if has_request_context() and request.path == XENOSAGA_PATH:
            kwargs["title"] = html_escape(XENOSAGA_TITLE)
            kwargs["metas"] = build_xenosaga_head_metadata(kwargs.get("metas", ""))
            kwargs["app_entry"] = (
                '<div id="react-entry-point">'
                f"{build_xenosaga_static_html()}"
                "</div>"
            )

        return super().interpolate_index(**kwargs)


def build_games_tree() -> list[dict[str, Any]]:
    """Build Mantine tree data from the registered Dash pages.

    Returns:
        A list of tree node dictionaries grouped by game. Leaf nodes store the
        Dash page path as their ``value`` so selection can drive navigation.
    """
    games: dict[str, list[dict[str, Any]]] = {}

    for page in page_registry.values():
        module: str = page["module"]  # e.g. "pages.expedition33.zonelevels"
        parts = module.split(".")[1:]  # drop leading "pages"
        if not parts or parts[0] == "home":
            continue

        game = parts[0]
        games.setdefault(game, []).append(page)

    items: list[dict[str, Any]] = []
    for game, pages in sorted(games.items(), key=lambda kv: kv[0]):
        children: list[dict[str, Any]] = []
        for page in sorted(pages, key=lambda p: p["name"]):
            children.append(
                {
                    "label": page["name"],   # must be JSON-serializable (string)
                    "value": page["path"],   # leaf value = path we can navigate to
                }
            )

        items.append(
            {
                "label": game.capitalize(),
                "value": f"game:{game}",     # avoid collisions with real paths
                "children": children,
            }
        )

    return items


# create the Dash app with the builtin pages support
app = LudexDash(
    __name__,
    description="An index of resources for various games.",
    external_scripts=[
        {
            "src": "https://plausible.automateordie.dev/js/pa-LPoOV2pIp1B60qeTlaXqj.js",
            "async": "async",
        }
    ],
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    pages_folder="games",
    suppress_callback_exceptions=True,  # tree lives in page layout, not top-level
    title="Ludex",
    use_pages=True,
)


def crawler_response(body: str, mimetype: str) -> Response:
    """Return a cacheable crawler resource with an explicit content type."""

    response = Response(body, mimetype=mimetype)
    response.headers["Cache-Control"] = "public, max-age=3600"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.server.get("/robots.txt")
def robots_txt() -> Response:
    """Advertise open crawling and the canonical sitemap location."""

    return crawler_response(
        "User-agent: *\nAllow: /\n\nSitemap: https://ludex.games/sitemap.xml\n",
        "text/plain",
    )


@app.server.get("/sitemap.xml")
def sitemap_xml() -> Response:
    """List canonical public Dash pages for search-engine discovery."""

    paths = {
        page["path"]
        for page in page_registry.values()
        if page.get("path") and not page.get("path_template")
    }
    ordered_paths = sorted(paths, key=lambda path: (path != "/", path))
    urls = "".join(
        f"<url><loc>{xml_escape(f'{SITE_ORIGIN}{path}')}</loc></url>"
        for path in ordered_paths
    )
    document = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"{urls}"
        "</urlset>"
    )
    return crawler_response(document, "application/xml")


@app.server.get("/llms.txt")
def llms_txt() -> Response:
    """Provide a concise machine-readable guide to Ludex's public content."""

    document = """# Ludex

> Ludex is a collection of searchable game databases, calculators, and reference pages.

Canonical site: https://ludex.games/

## Xenosaga Enemy Database

- [Xenosaga Enemy Database](https://ludex.games/xenosaga): A searchable and sortable reference containing 325 enemies from Xenosaga Episodes I, II, and III.
- The database includes HP, experience, weaknesses, resistances, item drops, stealable items, and episode-specific combat statistics.
- The page contains a complete server-rendered HTML version of the data for clients that do not execute JavaScript. JavaScript enables the interactive grid, filters, sorting, and enemy detail dialogs.

### Primary data sources

- [Episode I Enemies FAQ](https://gamefaqs.gamespot.com/ps2/519264-xenosaga-episode-i-der-wille-zur-macht/faqs/22927)
- [Episode II Enemy FAQ](https://www.ign.com/articles/2005/04/06/xenosaga-episode-ii-jenseits-von-gut-und-bose-enemy-faq-545281)
- [Episode III Enemy FAQ](https://gamefaqs.gamespot.com/ps2/929933-xenosaga-episode-iii-also-sprach-zarathustra/faqs/45192)

## Clair Obscur: Expedition 33

- [Skill Damage Reference](https://ludex.games/exp33/skilldamage)
- [Skill Damage Calculator](https://ludex.games/exp33/calculator)
- [Zone Level Reference](https://ludex.games/exp33/zonelevels)

## Project and corrections

- [Source code and documentation](https://github.com/perfectly-preserved-pie/ludex)
- Corrections: hey@ludex.games
"""
    return crawler_response(document, "text/plain")


@app.server.before_request
def redirect_legacy_dash_chunk() -> Response | None:
    """Redirect malformed, ID-prefixed DCC chunk requests to registered files.

    Some clients request Webpack chunk IDs as part of the filename, for example
    ``113.async-upload.js``. Dash rejects those paths with a noisy 500 response.
    Only redirect when the corresponding unprefixed file is registered by Dash.
    """
    match = LEGACY_DASH_CHUNK_PATH.fullmatch(request.path)
    if match is None:
        return None

    filename = match.group(1)
    registered_path = f"dcc/{filename}"
    if registered_path not in app.registered_paths.get("dash", set()):
        return None

    return redirect(
        f"/_dash-component-suites/dash/{registered_path}",
        code=307,
    )


@app.server.before_request
def redirect_noncanonical_xenosaga_path() -> Response | None:
    """Consolidate the trailing-slash Xenosaga URL into its canonical URL."""

    if request.path != f"{XENOSAGA_PATH}/":
        return None

    query_string = request.query_string.decode("utf-8")
    target = XENOSAGA_PATH
    if query_string:
        target = f"{target}?{query_string}"
    return redirect(target, code=308)


dmc.pre_render_color_scheme()


@dash.hooks.index()
def add_document_language(app_index: str) -> str:
    """Declare the document language after Mantine decorates the HTML tag."""

    return app_index.replace(
        "<html data-mantine-color-scheme=",
        '<html lang="en" data-mantine-color-scheme=',
        1,
    )


def home_layout() -> dbc.Container:
    """Build the home page layout.

    Returns:
        A fresh Bootstrap container for the home page. Rebuilding the layout on
        each render resets the tree selection so the same page can be selected
        again after navigating back.
    """
    return dbc.Container(
        [
            dcc.Location(id="url"),
            dbc.Row(
                dbc.Col(
                    dbc.Card(
                        [
                            html.H1("Ludex", className="card-title mb-2"),
                            html.I('Latin "ludus" (game) + dex (index)', className="d-block mb-2"),
                            html.P(
                                "A small index of game tools and reference pages.",
                                className="mb-3",
                            ),
                            html.Div(
                                [
                                    html.Span(
                                        [
                                            DashIconify(icon="octicon:mark-github-16"),
                                            html.A(
                                                "GitHub",
                                                href="https://github.com/perfectly-preserved-pie/ludex/tree/main",
                                                target="_blank",
                                            ),
                                        ],
                                        style={
                                            "display": "inline-flex",
                                            "alignItems": "center",
                                            "gap": "5px",
                                        },
                                    ),
                                    html.Span(
                                        [
                                            DashIconify(icon="streamline-color:send-email"),
                                            html.A(
                                                "hey@ludex.games",
                                                href="mailto:hey@ludex.games",
                                                target="_blank",
                                            ),
                                        ],
                                        style={
                                            "display": "inline-flex",
                                            "alignItems": "center",
                                            "gap": "5px",
                                        },
                                    ),
                                ],
                                style={
                                    "display": "flex",
                                    "alignItems": "center",
                                    "columnGap": "15px",
                                    "rowGap": "8px",
                                    "flexWrap": "wrap",
                                },
                            ),
                        ],
                        body=True,
                        id="title-card",
                    ),
                    width=12,
                ),
                className="mt-4 mb-3",
            ),
            dbc.Row(
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.P("Select a game to explore:", className="mb-0"),
                                dmc.Tree(
                                    id="games-tree",
                                    data=build_games_tree(),
                                    selectOnClick=True,
                                    clearSelectionOnOutsideClick=True,
                                    selected=[],
                                    expanded="*",  # expand all by default
                                ),
                            ]
                        )
                    ),
                    width=12,
                )
            ),
        ],
        fluid=True,
    )


register_page(__name__, path="/", name="Home", layout=home_layout)

app.layout = dmc.MantineProvider(
    dbc.Container(
        [
            dbc.Row(
                dbc.Col(
                    html.Div(
                        [
                            dcc.Link(
                                dbc.Button("Home", color="secondary", outline=True, className="py-1"),
                                href="/",
                                refresh=False,
                            ),
                            dmc.ColorSchemeToggle(
                                id="theme-toggle",
                                lightIcon=DashIconify(
                                    icon="radix-icons:sun",
                                    width=15,
                                    color="var(--mantine-color-yellow-8)",
                                ),
                                darkIcon=DashIconify(
                                    icon="radix-icons:moon",
                                    width=15,
                                    color="var(--mantine-color-yellow-6)",
                                ),
                                size="lg",
                            ),
                        ],
                        className="d-flex align-items-center gap-2",
                    ),
                    width=12,
                    className="py-3",
                )
            ),
            dash.page_container,
        ],
        fluid=True,
        className="dbc dmc",
    )
)


@callback(
    Output("url", "pathname"),
    Input("games-tree", "selected"),
    prevent_initial_call=True,
)
def navigate_from_tree(selected: list[str] | None) -> str:
    """Resolve a tree selection into a Dash pathname.

    Args:
        selected: The list of selected tree node values from the Mantine tree.

    Returns:
        The pathname for the selected leaf node.
    """
    if not selected:
        raise dash.exceptions.PreventUpdate

    value = selected[-1]
    if value.startswith("game:"):
        raise dash.exceptions.PreventUpdate

    return value

# For Gunicorn
server = app.server

if __name__ == "__main__":
    app.run(debug=True)
