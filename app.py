from __future__ import annotations
from dash import Input, Output, callback, dcc, html, page_registry, register_page
from typing import Any
import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash_iconify import DashIconify

def build_games_tree() -> list[dict[str, Any]]:
    """
    Build dmc.Tree data from Dash Pages registry.

    - Leaves use value=<page path> so selection can drive navigation.
    - Game grouping nodes use a prefixed value to guarantee uniqueness.
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
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,  # tree lives in page layout, not top-level
    title="Ludex",
    use_pages=True,
)

dmc.pre_render_color_scheme()

def home_layout() -> dbc.Container:
    """
    Build the Home page layout.

    Returns a fresh component tree on each render so `games-tree` starts with
    `selected=[]`, which allows selecting the same leaf again after navigating back.
    """
    return dbc.Container(
        [
            dcc.Location(id="url"),
            dbc.Row(
                dbc.Col(
                    dmc.Card(
                        dbc.CardBody(
                            [
                                html.H1("Ludex", className="mb-2"),
                                html.P(
                                    html.Em('Latin "ludus" (game) + dex (index)'),
                                    className="mb-0",
                                ),
                            ]
                        ),
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
                        className="d-flex justify-content-end py-3",
                    ),
                    width=12,
                )
            ),
            dash.page_container,
        ],
        fluid=True,
    )
)


@callback(
    Output("url", "pathname"),
    Input("games-tree", "selected"),
    prevent_initial_call=True,
)
def navigate_from_tree(selected: list[str] | None) -> str:
    """
    Navigate to the selected leaf node (page path).
    Parent nodes are ignored (they use 'game:<name>' values).
    """
    if not selected:
        raise dash.exceptions.PreventUpdate

    value = selected[-1]
    if value.startswith("game:"):
        raise dash.exceptions.PreventUpdate

    return value


if __name__ == "__main__":
    app.run(debug=True)
