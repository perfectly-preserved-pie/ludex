"""Browser-side analytics wired to completed Dash updates."""

from dash import ClientsideFunction, Input, Output, State, dcc


ANALYTICS_STORES = [dcc.Store(id=f"analytics-{name}") for name in ("calculator", "import", "xenosaga")]


def register_analytics(app):
    app.clientside_callback(
        ClientsideFunction(namespace="analytics", function_name="calculator"),
        Output("analytics-calculator", "data"),
        Input("exp33-calculator-result-body", "children"),
        State("exp33-calculator-character", "value"),
        State("exp33-calculator-skill", "value"),
        prevent_initial_call=True,
    )
    app.clientside_callback(
        ClientsideFunction(namespace="analytics", function_name="saveImport"),
        Output("analytics-import", "data"),
        Input("exp33-calculator-save-import-status", "children"),
        State("exp33-calculator-save-import-status", "color"),
        State("exp33-calculator-save-import-status", "is_open"),
        prevent_initial_call=True,
    )
    app.clientside_callback(
        ClientsideFunction(namespace="analytics", function_name="xenosaga"),
        Output("analytics-xenosaga", "data"),
        Input("xenosaga-tabs", "active_tab"),
        Input("xenosaga-grid", "filterModel"),
        Input("xenosaga-grid", "cellClicked"),
        prevent_initial_call=True,
    )
