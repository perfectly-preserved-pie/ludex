import gzip
import json
import re
from xml.etree import ElementTree

import pytest
from dash import page_registry


@pytest.mark.parametrize("path", ["/", "/xenosaga", "/exp33/skilldamage", "/exp33/zonelevels", "/exp33/calculator"])
def test_pages_serve_react19(client, path):
    response = client.get(path)
    assert response.status_code == 200
    assert '<html lang="en"' in response.text
    assert "react@19" in response.text


def test_xenosaga_has_crawlable_data_and_canonical_metadata(client):
    response = client.get("/xenosaga")
    assert '<link rel="canonical" href="https://ludex.games/xenosaga"' in response.text
    assert response.text.count('<th scope="row">') == 325
    assert 'property="og:title"' in response.text
    redirect = client.get("/xenosaga/?search=gnosis")
    assert redirect.status_code == 308
    assert redirect.location == "/xenosaga?search=gnosis"


def test_sitemap_matches_registered_pages(client, dash_app):
    response = client.get("/sitemap.xml")
    document = ElementTree.fromstring(response.data)
    locations = {element.text for element in document.findall("{*}url/{*}loc")}
    assert locations == {f"https://ludex.games{page['path']}" for page in page_registry.values()}
    assert response.headers["X-Content-Type-Options"] == "nosniff"


@pytest.mark.parametrize("path, content_type", [("/robots.txt", "text/plain"), ("/llms.txt", "text/plain")])
def test_crawler_resources(client, path, content_type):
    response = client.get(path)
    assert response.status_code == 200
    assert response.mimetype == content_type
    assert "https://ludex.games/" in response.text


@pytest.mark.parametrize("path", ["/xenosaga", "/_dash-layout", "/_dash-dependencies"])
def test_gzip_responses_preserve_content_and_reduce_transfer(client, path):
    original = client.get(path)
    compressed = client.get(path, headers={"Accept-Encoding": "gzip"})
    assert compressed.status_code == 200
    assert compressed.headers["Content-Encoding"] == "gzip"
    decoded = gzip.decompress(compressed.data)
    # Dash signs a fresh end_id for each HTML request.
    normalize = lambda body: re.sub(rb'"end_id":"[^"]+"', b'"end_id":"TOKEN"', body)
    assert normalize(decoded) == normalize(original.data)
    assert len(compressed.data) < len(original.data) * 0.5


def test_all_index_script_bundles_are_registered(client):
    response = client.get("/")
    paths = re.findall(r'<script[^>]+src="(/_dash-component-suites/[^\"]+)"', response.text)
    assert paths
    for path in paths:
        bundle = client.get(path)
        assert bundle.status_code == 200, path
        assert bundle.mimetype in {"text/javascript", "application/javascript"}


def test_legacy_chunk_redirects_only_registered_files(client, dash_app):
    paths = dash_app.registered_paths["dash"]
    chunk = next(path for path in paths if path.startswith("dcc/async-") and path.endswith(".js"))
    response = client.get(f"/_dash-component-suites/dash/dcc/113.{chunk.removeprefix('dcc/')}")
    assert response.status_code == 307
    assert response.location == f"/_dash-component-suites/dash/{chunk}"
    assert client.get(response.location).status_code == 200


def test_oversized_callback_request_is_rejected(client, dash_app):
    size = dash_app.server.config["MAX_CONTENT_LENGTH"] + 1
    response = client.post("/_dash-update-component", data=b" " * size, content_type="application/json")
    assert response.status_code == 413


def test_detail_callbacks_do_not_upload_table_state(client):
    dependencies = client.get("/_dash-dependencies").json
    details = [item for item in dependencies if "modal-content.children" in item["output"]]
    assert len(details) == 2
    assert all(not item["state"] for item in details)


def post_callback(client, dash_app, component_id, inputs, changed):
    key = next(key for key in dash_app.callback_map if f"{component_id}." in key)
    outputs = dash_app.callback_map[key]["output"]
    if not isinstance(outputs, list):
        outputs = [outputs]
    return client.post("/_dash-update-component", json={
        "output": key,
        "outputs": [{"id": output.component_id, "property": output.component_property} for output in outputs],
        "inputs": [{"id": id_, "property": prop, "value": value} for id_, prop, value in inputs],
        "state": [],
        "changedPropIds": [changed],
    })


@pytest.mark.parametrize("grid_id, tabs_id, tab, label", [
    ("xenosaga-grid", "xenosaga-tabs", "ep3", "Name"),
    ("exp33-skill-damage-grid", "exp33-skill-damage-tabs", "verso", "Skill"),
])
def test_grid_tab_and_detail_callbacks(client, dash_app, grid_id, tabs_id, tab, label):
    response = post_callback(client, dash_app, grid_id, [(tabs_id, "active_tab", tab)], f"{tabs_id}.active_tab")
    assert response.status_code == 200
    grid = response.json["response"][grid_id]
    assert grid["columnSize"] == "autoSize"
    rows = grid["rowData"]
    assert rows and all(row["_row_id"].startswith(tab + ":") for row in rows)
    assert len({row["_row_id"] for row in rows}) == len(rows)
    prefix = "xenosaga" if grid_id == "xenosaga-grid" else "exp33-skill-damage"
    clicked = rows[-1]
    # rowIndex is deliberately wrong: sorted/paginated positions aren't row identities.
    click = {"rowId": clicked["_row_id"], "rowIndex": 0, "data": {label: "forged"}}
    inputs = [(grid_id, "cellClicked", click), (f"{prefix}-close", "n_clicks", 0)]
    response = post_callback(client, dash_app, f"{prefix}-modal", inputs, f"{grid_id}.cellClicked")
    assert response.status_code == 200
    detail = response.json["response"]
    assert detail[f"{prefix}-modal"]["is_open"] is True
    assert detail[f"{prefix}-modal-header"]["children"]["props"]["children"] == clicked[label]
    assert "_row_id" not in json.dumps(detail[f"{prefix}-modal-content"])
    close = post_callback(client, dash_app, f"{prefix}-modal", inputs, f"{prefix}-close.n_clicks")
    assert close.json["response"][f"{prefix}-modal"]["is_open"] is False
    inputs[0] = (grid_id, "cellClicked", {"rowId": "not-a-row"})
    assert post_callback(client, dash_app, f"{prefix}-modal", inputs, f"{grid_id}.cellClicked").status_code == 204
