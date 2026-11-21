from __future__ import annotations

import re
from html import escape as html_escape
from typing import Any
from urllib.parse import quote_from_bytes

import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import Input, Output, callback, dcc, html, page_registry, register_page
from dash_iconify import DashIconify
from flask import Response, abort, has_request_context, redirect, request
from helpers.seo import (
    PROJECT_INFO_PATH,
    PROJECT_SECTIONS,
    PROJECT_URL,
    SITE_DESCRIPTION,
    alternate_links,
    build_initial_page,
    build_markdown,
    build_page_structured_data,
    build_sitemap_urls,
    build_social_head_metadata,
)
from helpers.analytics import ANALYTICS_STORES, register_analytics
from games.xenosaga.seo import (
    SITE_ORIGIN,
    XENOSAGA_DESCRIPTION,
    XENOSAGA_PATH,
    XENOSAGA_TITLE,
    build_xenosaga_head_metadata,
    build_xenosaga_static_html,
    build_xenosaga_markdown_details,
    xenosaga_dataset_entity,
)


LEGACY_DASH_CHUNK_PATH = re.compile(
    r"^/_dash-component-suites/dash/dcc/\d+\.(async-[A-Za-z0-9_-]+\.js(?:\.map)?)$"
)

# Mantine Components 3 requires React 19 (Dash 4.5 still defaults to React 18).
dash._dash_renderer._set_react_version("19.2.4")


class LudexDash(dash.Dash):
    """Dash application with crawlable first-response content for key pages."""

    def interpolate_index(self, **kwargs: str) -> str:
        """Add page-specific server HTML before Dash hydrates the application."""

        if has_request_context() and request.path != XENOSAGA_PATH:
            page = next(
                (page for page in page_registry.values() if page.get("path") == request.path),
                None,
            )
            if page is not None:
                title = page["title"]
                kwargs["title"] = html_escape(title)
                kwargs["metas"] = build_social_head_metadata(
                    kwargs.get("metas", ""),
                    title=title,
                    description=page.get("description") or SITE_DESCRIPTION,
                    path=page["path"],
                )
                entities = ()
                if request.path == "/":
                    calculator = public_pages()["/exp33/calculator"]
                    entities = (
                        xenosaga_dataset_entity(),
                        {
                            "@type": "WebApplication",
                            "name": calculator["title"],
                            "description": calculator["description"],
                            "url": f'{SITE_ORIGIN}{calculator["path"]}',
                            "applicationCategory": "GameApplication",
                        },
                    )
                kwargs["metas"] += build_page_structured_data(page, *entities)
                kwargs["app_entry"] = (
                    '<div id="react-entry-point">'
                    f'{build_initial_page(page, public_pages())}</div>'
                )

        if has_request_context() and request.path == XENOSAGA_PATH:
            kwargs["title"] = html_escape(XENOSAGA_TITLE)
            kwargs["metas"] = build_xenosaga_head_metadata(kwargs.get("metas", ""))
            kwargs["app_entry"] = (
                '<div id="react-entry-point">'
                '<div id="xenosaga-startup-screen" role="status" aria-live="polite">'
                '<span class="xenosaga-startup-spinner" aria-hidden="true"></span>'
                "Loading the interactive enemy database…"
                "</div>"
                f"{build_xenosaga_static_html()}"
                "</div>"
            )

        if has_request_context() and request.path in public_pages():
            kwargs["metas"] += "".join(
                f'<link rel="alternate" type="{media_type}" href="{url}">'
                for url, media_type in alternate_links(request.path)
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
        if not parts or parts[0] in {"home", "about"}:
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
    compress=True,
    description=SITE_DESCRIPTION,
    image="social-preview.png",
    external_scripts=[
        {
            "src": "https://plausible.automateordie.dev/js/pa-LPoOV2pIp1B60qeTlaXqj.js",
            "async": "async",
        },
        {
            "src": "/analytics/script.js?siteId=63c3e597eb6d",
            "defer": "defer",
        },
    ],
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    pages_folder="games",
    suppress_callback_exceptions=True,  # tree lives in page layout, not top-level
    title="Ludex",
    use_pages=True,
)

# A 10 MiB save expands to about 13.4 MiB in Dash's base64 JSON upload.
app.server.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024


@app.server.get("/analytics/script.js")
def analytics_script_fallback() -> Response:
    """Serve valid JavaScript when the deployment's analytics proxy is absent."""

    # Production's reverse proxy serves the tracker before requests reach Dash.
    # Locally, avoid Dash's HTML catch-all being parsed as a JavaScript bundle.
    response = Response("// Analytics proxy is unavailable.\n", mimetype="text/javascript")
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


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
        "User-agent: *\nAllow: /\n"
        "Content-Signal: search=yes, ai-input=yes, ai-train=no\n\n"
        f"Sitemap: {SITE_ORIGIN}/sitemap.xml\n",
        "text/plain",
    )


def public_pages() -> dict[str, dict[str, Any]]:
    """Map canonical paths to the registered public pages."""

    return {
        page["path"]: page
        for page in page_registry.values()
        if page.get("path") and not page.get("path_template")
    }


@app.server.after_request
def advertise_page_alternates(response: Response) -> Response:
    """Expose discovery links to clients that only inspect response headers."""

    if response.status_code == 200 and request.path in public_pages():
        for url, media_type in alternate_links(request.path):
            response.headers.add("Link", f'<{url}>; rel="alternate"; type="{media_type}"')
    return response


@app.server.get("/sitemap.xml")
def sitemap_xml() -> Response:
    """List canonical public Dash pages for search-engine discovery."""

    urls = build_sitemap_urls(sorted(public_pages()))
    document = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"{urls}"
        "</urlset>"
    )
    return crawler_response(document, "application/xml")


def page_guide(path: str, page: dict[str, Any], *, frontmatter: bool = True) -> str:
    """Render a page guide and attach the complete dataset for Xenosaga."""

    details = build_xenosaga_markdown_details() if path == XENOSAGA_PATH else ""
    return build_markdown(page, details, frontmatter=frontmatter)


@app.server.get("/index.md", defaults={"page_path": "index"})
@app.server.get("/<path:page_path>.md")
def page_markdown(page_path: str) -> Response:
    """Serve the public Markdown companion for a registered page."""

    path = "/" if page_path == "index" else f"/{page_path}"
    page = public_pages().get(path)
    if page is None:
        abort(404)
    response = crawler_response(page_guide(path, page), "text/markdown")
    response.headers["Link"] = f'<{SITE_ORIGIN}{path}>; rel="canonical"'
    return response


@app.server.get("/llms-full.txt")
def llms_full_txt() -> Response:
    """Serve the page guides together with the full Xenosaga dataset."""

    pages = public_pages()
    ordered_paths = ["/", XENOSAGA_PATH, *(path for path in sorted(pages) if path not in {"/", XENOSAGA_PATH})]
    guides = (page_guide(path, pages[path], frontmatter=False) for path in ordered_paths)
    return crawler_response("\n---\n\n".join(guides), "text/plain")


@app.server.get("/llms.txt")
def llms_txt() -> Response:
    """Provide a concise machine-readable guide to Ludex's public content."""

    document = """# Ludex

> Ludex is a collection of searchable game databases, calculators, and reference pages.

Canonical site: https://ludex.games/

## When to use Ludex

- Use Ludex when comparing Xenosaga enemy stats, weaknesses, drops, and stealable items, or when looking up Expedition 33 skills, build damage estimates, and recommended zone levels.
- Cite the relevant game page. For Xenosaga, include the episode and enemy name because enemies and available statistics vary across episodes.

- [Expanded text guide](https://ludex.games/llms-full.txt): All page guides and Xenosaga enemy tables in one document.
- [Xenosaga Markdown edition](https://ludex.games/xenosaga.md): All enemy records with episode-specific statistics and source links.

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
- [About, contact, and privacy](https://ludex.games/about)
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
    for registered_path in app.registered_paths.get("dash", ()):
        if registered_path == f"dcc/{filename}":
            return redirect(f"/_dash-component-suites/dash/{registered_path}", code=307)
    return None


@app.server.before_request
def enforce_public_page_routes() -> Response | None:
    """Redirect slash variants and return a genuine 404 for unknown Dash pages."""

    if request.endpoint != "/<path:path>":
        return None
    pages = public_pages()
    if request.path in pages:
        return None
    page = pages.get(request.path.rstrip("/"))
    if page is not None:
        target = page["path"]
        # Keep the original parameter order and percent escapes. The registered
        # path fixes the destination, and quoting keeps query bytes in the query.
        query = quote_from_bytes(request.query_string, safe="!$&'()*+,/:;=?@%")
        return redirect(target + "?" + query if query else target, code=308)
    abort(404)


@app.server.errorhandler(404)
def not_found(error) -> Response:
    """Keep the 404 status and provide Markdown to clients that request it."""

    response = error.get_response()
    if request.accept_mimetypes.best_match(("text/html", "text/markdown")) == "text/markdown":
        response = Response(
            f"# Page not found\n\nThis URL does not exist on Ludex. [Return to Ludex]({SITE_ORIGIN}/).\n",
            status=404,
            mimetype="text/markdown",
        )
    response.vary.add("Accept")
    return response


dmc.pre_render_color_scheme()


@dash.hooks.index()
def add_document_language(app_index: str) -> str:
    """Declare the document language after Mantine decorates the HTML tag."""

    app_index = app_index.replace(
        "<html data-mantine-color-scheme=",
        '<html lang="en" data-mantine-color-scheme=',
        1,
    )
    if has_request_context() and request.path == XENOSAGA_PATH:
        startup_handoff = """<style>
            #xenosaga-startup-screen { display: none; }
            html.ludex-xenosaga-loading #xenosaga-static-content { display: none !important; }
            html.ludex-xenosaga-loading #xenosaga-startup-screen {
                align-items: center;
                display: flex;
                gap: .75rem;
                justify-content: center;
                min-height: 55vh;
                color: #495057;
                font: 1rem system-ui, sans-serif;
            }
            .xenosaga-startup-spinner {
                animation: ludex-spin .8s linear infinite;
                border: 3px solid #dee2e6;
                border-top-color: #0d6efd;
                border-radius: 50%;
                height: 1.25rem;
                width: 1.25rem;
            }
            @keyframes ludex-spin { to { transform: rotate(360deg); } }
        </style>
        <script>
            (() => {
                const className = "ludex-xenosaga-loading";
                document.documentElement.classList.add(className);
                const finish = () => {
                    if (document.querySelector("#xenosaga-grid")) {
                        document.documentElement.classList.remove(className);
                        observer.disconnect();
                        clearTimeout(fallback);
                    }
                };
                const observer = new MutationObserver(finish);
                observer.observe(document.documentElement, {childList: true, subtree: true});
                const fallback = setTimeout(() => {
                    document.documentElement.classList.remove(className);
                    observer.disconnect();
                }, 10000);
            })();
        </script>"""
        app_index = app_index.replace("</head>", f"{startup_handoff}</head>", 1)
    return app_index


def home_layout() -> dbc.Container:
    """Build the home page layout.

    Returns:
        A fresh Bootstrap container for the home page. Rebuilding the layout on
        each render resets the tree selection so the same page can be selected
        again after navigating back.
    """
    return dbc.Container(
        [
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
                                                href=PROJECT_URL,
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
            html.Footer(
                [
                    dcc.Link(title, href=f"{PROJECT_INFO_PATH}#{slug}", refresh=False)
                    for slug, title, *_ in PROJECT_SECTIONS
                ],
                className="d-flex gap-3 mt-3 small",
            ),
        ],
        fluid=True,
    )


register_page("pages.home", path="/", name="Home", title="Ludex | Game Tools & Reference", description=SITE_DESCRIPTION, layout=home_layout)

register_page(
    "pages.about",
    path=PROJECT_INFO_PATH,
    title="Project Information | Ludex",
    description="About Ludex, how to contact the project, and how site analytics and calculator save imports are handled.",
    layout=html.Main(
        [
            html.H1("Project Information"),
            *[
                html.Section(
                    [
                        html.H2(title, className="h5"),
                        html.P(
                            [body, " ", html.A(email[0], href=f"mailto:{email[0]}"), "."]
                            if email else body
                        ),
                    ],
                    id=slug,
                    className="mt-4",
                )
                for slug, title, body, *email in PROJECT_SECTIONS
            ],
        ],
        className="container py-4",
    ),
)

app.layout = dmc.MantineProvider(
    dbc.Container(
        [
            *ANALYTICS_STORES,
            dcc.Location(id="url", refresh="callback-nav"),
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

register_analytics(app)

# For Gunicorn
server = app.server

if __name__ == "__main__":
    app.run(debug=True)
