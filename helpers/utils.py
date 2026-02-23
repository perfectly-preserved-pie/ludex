import dash_bootstrap_components as dbc
from dash import html

def make_info_card(text: str):
    """return a simple bootstrap card with the given text"""
    return dbc.Card(dbc.CardBody(html.P(text)))
