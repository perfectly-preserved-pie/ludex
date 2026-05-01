from __future__ import annotations

from typing import Any

AUTO_SIZE_COLUMNS = "autoSize"


def default_grid_column_config() -> dict[str, Any]:
    """Return shared Dash AG Grid column defaults."""

    return {
        "defaultColDef": {"filter": True, "sortable": True, "resizable": True},
        "columnSize": AUTO_SIZE_COLUMNS,
        "columnSizeOptions": {"skipHeader": False},
    }


def default_dash_grid_options(**options: Any) -> dict[str, Any]:
    """Return shared Dash AG Grid options merged with page-specific options."""

    return {
        "suppressColumnVirtualisation": True,
        **options,
    }
