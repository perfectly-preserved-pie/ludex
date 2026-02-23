# filepath: app.py
import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

# create the Dash app with the builtin pages support
app = dash.Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    #suppress_callback_exceptions=True,
)

app.layout = dbc.Container(
    [
        dbc.NavbarSimple(
            children=[
                dbc.NavItem(dbc.NavLink(page["name"], href=page["path"]))
                for page in dash.page_registry.values()
            ],
            brand="Multi‑Page Demo",
            color="dark",
            dark=True,
        ),
        html.Hr(),
        dash.page_container,
    ],
    fluid=True,
)

if __name__ == "__main__":
    app.run(debug=True)
