from dash import html, dcc, page_registry, register_page
import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc

def build_games_tree():
    games: dict[str, list[dict]] = {}
    # walk the registry looking for modules under `pages.<game>`
    for p in page_registry.values():
        mod = p["module"]            # e.g. "pages.expedition33.zonelevels"
        parts = mod.split(".")[1:]   # chop off the leading "pages"
        if not parts or parts[0] == "home":
            continue                 # skip the home page itself
        game = parts[0]
        games.setdefault(game, []).append(p)

    items = []
    for game, pages in sorted(games.items()):
        children = []
        for p in sorted(pages, key=lambda x: x["name"]):
            children.append(
                {
                    "label": dcc.Link(p["name"], href=p["path"],
                                      style={"textDecoration": "none"}),
                    "value": p["path"],
                }
            )
        items.append({"label": game.capitalize(), "value": game,
                      "children": children})
    return items

# create the Dash app with the builtin pages support
app = dash.Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    #suppress_callback_exceptions=True,
)

app.layout = dmc.MantineProvider(
    dbc.Container(
        [
            dash.page_container,
        ],
        fluid=True,
    )
)

# home‑page layout moved here
home_layout = html.Div(
    [
        html.H1("Home"),
        html.P("Select a game to explore:"),
        dmc.Tree(
            id="games-tree",
            data=build_games_tree(),
        ),
    ]
)

register_page(__name__, path="/", name="Home", layout=home_layout)

if __name__ == "__main__":
    app.run(debug=True)