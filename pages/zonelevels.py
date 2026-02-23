from dash import dcc, html
import dash_ag_grid as dag
import dash_bootstrap_components as dbc

zones = [
    {
        "name": "Gestral Beach",
        "level": 1
    },
    {
        "name": "Blades' Graveyard",
        "level": 1
    },
    {
        "name": "Boat Graveyard",
        "level": 1
    },
    {
        "name": "Twilight Quarry",
        "level": 1
    },
    {
        "name": "Lost Woods",
        "level": 1
    },
    {
        "name": "Ancient Gestral City",
        "level": 1
    },
    {
        "name": "The Meadows",
        "level": 1
    },
    {
        "name": "White Tree",
        "level": 1
    },
    {
        "name": "Spring Meadows",
        "level": 3
    },
    {
        "name": "Flying Waters",
        "level": 8
    },
    {
        "name": "Flying Casino",
        "level": 10
    },
    {
        "name": "Ancient Sanctuary",
        "level": 12
    },
    {
        "name": "The Small Bourgeon",
        "level": 13
    },
    {
        "name": "Gestral Village",
        "level": 15
    },
    {
        "name": "Esquie's Nest",
        "level": 16
    },
    {
        "name": "Hidden Gestral Arena",
        "level": 16
    },
    {
        "name": "Stone Wave Cliffs",
        "level": 19
    },
    {
        "name": "Yellow Harvest",
        "level": 21
    },
    {
        "name": "Stone Wave Cliffs Cave",
        "level": 22
    },
    {
        "name": "Forgotten Battlefield",
        "level": 23
    },
    {
        "name": "Monoco's Station",
        "level": 25
    },
    {
        "name": "Crushing Cavern",
        "level": 27
    },
    {
        "name": "Old Lumiere",
        "level": 28
    },
    {
        "name": "Esoteric Ruins",
        "level": 28
    },
    {
        "name": "Abbest Cave",
        "level": 30
    },
    {
        "name": "The Carousel",
        "level": 30
    },
    {
        "name": "Stone Quarry",
        "level": 30
    },
    {
        "name": "Visages",
        "level": 32
    },
    {
        "name": "Coastal Cave",
        "level": 36
    },
    {
        "name": "Sirene",
        "level": 37
    },
    {
        "name": "Sinister Cave",
        "level": 38
    },
    {
        "name": "The Monolith",
        "level": 40
    },
    {
        "name": "Falling Leaves",
        "level": 41
    },
    {
        "name": "The Barrier",
        "level": 41
    },
    {
        "name": "Monolith Peak",
        "level": 43
    },
    {
        "name": "Inside The Monolith",
        "level": 43
    },
    {
        "name": "Lumière",
        "level": 48
    },
    {
        "name": "Crimson Forest",
        "level": 52
    },
    {
        "name": "Endless Tower",
        "level": 55
    },
    {
        "name": "White Sands",
        "level": 55
    },
    {
        "name": "The Canvas",
        "level": 55
    },
    {
        "name": "Floating Cemetery",
        "level": 55
    },
    {
        "name": "The Reacher",
        "level": 58
    },
    {
        "name": "The Chosen Path",
        "level": 60
    },
    {
        "name": "Red Woods",
        "level": 60
    },
    {
        "name": "Sky Island",
        "level": 60
    },
    {
        "name": "Sacred River",
        "level": 60
    },
    {
        "name": "Sirène's Dress",
        "level": 60
    },
    {
        "name": "Frozen Hearts",
        "level": 63
    },
    {
        "name": "Isle of the Eyes",
        "level": 65
    },
    {
        "name": "The Crows",
        "level": 65
    },
    {
        "name": "Dark Shores",
        "level": 68
    },
    {
        "name": "Endless Night Sanctuary",
        "level": 73
    },
    {
        "name": "Dark Gestral Arena",
        "level": 75
    },
    {
        "name": "The Fountain",
        "level": 80
    },
    {
        "name": "Flying Manor",
        "level": 83
    },
    {
        "name": "Painting Workshop",
        "level": 90
    },
    {
        "name": "Sunless Cliffs",
        "level": 92
    },
    {
        "name": "Renoir's Drafts",
        "level": 93
    },
    {
        "name": "The Abyss",
        "level": 99
    }
]

grid = dag.AgGrid(
    rowData=zones,
    columnDefs=[
        {"field": "name", "headerName": "Zone", "filter": "agTextColumnFilter"},
        {"field": "level", "headerName": "Level", "filter": "agNumberColumnFilter"},
    ],
    defaultColDef={"filter": True, "sortable": True, "resizable": True},   
    dashGridOptions = {"domLayout": "autoHeight"}, # Fill the height of the grid to fit the number of rows
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
        dcc.Markdown("Here is a list of all the zones in the game, along with their recommended levels:"),
        grid
    ]
)

from dash import register_page
register_page(__name__, path="/zonelevels", name="Zone Levels", layout=layout)
