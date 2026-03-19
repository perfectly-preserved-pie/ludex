from __future__ import annotations
from dash import Input, Output, callback, dcc, html, page_registry, register_page
from typing import Any
import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash_iconify import DashIconify

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
app = dash.Dash(
    __name__,
    description="An index of resources for various games.",
    external_scripts=[
        {
            "src": "https://plausible.automateordie.io/js/pa-LPoOV2pIp1B60qeTlaXqj.js",
            "async": "async",
        }
    ],
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    pages_folder="games",
    suppress_callback_exceptions=True,  # tree lives in page layout, not top-level
    title="Ludex",
    use_pages=True,
)

dmc.pre_render_color_scheme()

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
