from dash import dcc, html
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from assets.expedition33.zonelevels_mapping import zones

# Dark theme for ag-grid
# https://www.dash-mantine-components.com/dash-ag-grid#dash-ag-grid-%E2%89%A5-v33
ag_grid_theme = {
    "function": (
        "themeQuartz.withParams({"
        "accentColor: 'var(--mantine-primary-color-filled)', "
        "backgroundColor: 'var(--mantine-color-body)', "
        "foregroundColor: 'var(--mantine-color-text)', "
        "fontFamily: 'var(--mantine-font-family)', "
        "headerFontWeight: 600"
        "})"
    )
}

grid = dag.AgGrid(
    rowData=zones,
    columnDefs=[
        {"field": "name", "headerName": "Zone", "filter": "agTextColumnFilter"},
        {"field": "level", "headerName": "Level", "filter": "agNumberColumnFilter"},
    ],
    defaultColDef={"filter": True, "sortable": True, "resizable": True},
    dashGridOptions={
        "domLayout": "autoHeight", # Fill the height of the grid to fit the number of rows
        "theme": ag_grid_theme,
    },
)

layout = html.Div(
    [
        html.H1("Zone Levels"),
        dbc.Alert(
            html.Span([
                "Data courtesy of ",
                html.A(
                    "@ElNin",
                    href="https://www.reddit.com/r/expedition33/comments/1ny33e6/zone_levels_datamined_by_elnin_on_discord/",
                    target="_blank",
                    rel="noopener noreferrer"
                ),
                " (Discord)"
            ]),
            color="info",
            className="mt-2"
        ),
        dcc.Markdown("Here is a list of all the zones in the game, along with their recommended levels. You can use the filters to find zones that are appropriate for your current level or search for a specific name."),
        grid
    ]
)

from dash import register_page
register_page(__name__, path="/zonelevels", name="Zone Levels", layout=layout)
