import re

import pytest
from playwright.sync_api import expect


pytestmark = pytest.mark.browser


def test_home_tree_navigation_and_theme(page, live_url):
    page.goto(live_url)
    expect(page.get_by_role("heading", name="Ludex", exact=True)).to_be_visible()
    scheme = page.locator("html").get_attribute("data-mantine-color-scheme")
    page.locator("#theme-toggle").click()
    expect(page.locator("html")).not_to_have_attribute("data-mantine-color-scheme", scheme)
    page.get_by_text("Enemy Database", exact=True).click()
    expect(page).to_have_url(live_url + "/xenosaga")
    expect(page.locator("#xenosaga-grid .ag-cell[col-id='Name']").first).to_be_visible()
    page.get_by_role("link", name="Home", exact=True).click()
    expect(page).to_have_url(live_url + "/")
    page.get_by_text("Enemy Database", exact=True).click()
    expect(page).to_have_url(live_url + "/xenosaga")
    expect(page.locator("#xenosaga-grid .ag-cell[col-id='Name']").first).to_be_visible()


@pytest.mark.parametrize("episode", ["Episode I", "Episode II", "Episode III"])
def test_enemy_grid_sorted_filtered_click_uses_correct_row(page, live_url, episode):
    page.goto(live_url + "/xenosaga")
    page.get_by_role("tab", name=episode, exact=True).click()
    grid = page.locator("#xenosaga-grid")
    cells = grid.locator(".ag-cell[col-id='Name']")
    expect(cells.first).to_be_visible()
    grid.locator(".ag-header-cell[col-id='Name'] .ag-header-cell-label").click()
    grid.locator(".ag-header-cell[col-id='Name'] .ag-header-cell-label").click()
    expected = cells.first.inner_text()
    page.evaluate("""async (name) => {
        const api = await dash_ag_grid.getApiAsync('xenosaga-grid');
        api.setFilterModel({Name: {filterType: 'text', type: 'equals', filter: name}});
    }""", expected)
    expect(cells.first).to_have_text(expected)
    cells.first.click()
    modal = page.locator(".modal.show")
    expect(modal.get_by_role("heading", name=expected, exact=True)).to_be_visible()
    expect(modal).not_to_contain_text("_row_id")
    modal.locator(".modal-footer").get_by_role("button", name="Close", exact=True).click()
    expect(modal).to_have_count(0)


@pytest.mark.parametrize("character", ["Gustave", "Lune", "Maelle", "Monoco", "Sciel", "Verso"])
def test_skill_tabs_and_detail_dialog(page, live_url, character):
    page.goto(live_url + "/exp33/skilldamage")
    page.get_by_role("tab", name=character, exact=True).click()
    grid = page.locator("#exp33-skill-damage-grid")
    # Wait for the selected character's data, not the previous tab's rows.
    expect(grid.locator(f".ag-row[row-id^='{character.lower()}:']").first).to_be_visible()
    expect(grid).not_to_contain_text("Invalid Number")
    grid.locator(".ag-header-cell[col-id='Skill'] .ag-header-cell-label").click()
    expect(grid.locator(".ag-header-cell[col-id='Skill']")).to_have_attribute("aria-sort", "ascending")
    row_id = grid.locator(".ag-row[row-index='0']").get_attribute("row-id")
    cell = grid.locator(f".ag-row[row-id='{row_id}'] .ag-cell[col-id='Skill']")
    expected = cell.inner_text()
    requests = []
    page.on("request", lambda request: requests.append(request.post_data_json)
            if request.url.split("?", 1)[0].endswith("/_dash-update-component") else None)
    cell.click()
    modal = page.locator(".modal.show")
    expect(modal.get_by_role("heading", name=expected, exact=True)).to_be_visible()
    detail_requests = [request for request in requests if "modal-content" in request["output"]]
    assert detail_requests and not detail_requests[-1].get("state")
    assert len(str(detail_requests[-1])) < 2000
    expect(modal).not_to_contain_text("_row_id")


def test_zone_level_number_filter(page, live_url):
    page.goto(live_url + "/exp33/zonelevels")
    levels = page.locator(".ag-cell[col-id='level']")
    expect(levels.first).to_be_visible()
    before = levels.count()
    page.locator(".ag-header-cell[col-id='level'] .ag-header-cell-filter-button").click()
    filter_input = page.get_by_role("spinbutton", name="Filter Value").first
    filter_input.fill("20")
    expect(levels).to_have_count(0)
    expect(page.locator(".ag-overlay").get_by_text("No Matching Rows", exact=True)).to_be_visible()
    filter_input.fill("3")
    expect(levels.first).to_have_text("3")
    expect(levels).to_have_count(1)
    assert before > 1


def test_calculator_updates_and_rejects_invalid_save(page, live_url):
    page.goto(live_url + "/exp33/calculator")
    result = page.locator("#exp33-calculator-result-body")
    expect(result.get_by_role("heading", name="Lightning Dance", exact=True)).to_be_visible()
    attack = page.locator("#exp33-calculator-attack")
    attack.fill("1000")
    attack.press("Tab")
    expect(result.get_by_role("heading", name="3,600", exact=True)).to_be_visible()
    attack.fill("2000")
    attack.press("Tab")
    expect(result.get_by_role("heading", name="7,200", exact=True)).to_be_visible()
    page.locator("#exp33-calculator-character").click()
    page.get_by_role("option", name="Gustave", exact=True).click()
    expect(result.get_by_role("heading", name="Overcharge 0 Charges", exact=True)).to_be_visible()
    page.locator("#exp33-calculator-save-upload input[type=file]").set_input_files({
        "name": "invalid.sav", "mimeType": "application/octet-stream", "buffer": b"not a save",
    })
    status = page.locator("#exp33-calculator-save-import-status")
    expect(status).to_be_visible()
    expect(status).to_contain_text(re.compile("could not be parsed|could not be imported", re.I))
