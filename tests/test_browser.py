import re

import pytest
from playwright.sync_api import expect


pytestmark = pytest.mark.browser


def test_home_tree_navigation_and_theme(page, live_url):
    page.goto(live_url)
    expect(page.get_by_role("heading", name="Ludex", exact=True)).to_be_visible()
    document_requests = []

    def track_document_request(request):
        if request.resource_type == "document":
            document_requests.append(request.url)

    page.on("request", track_document_request)
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
    assert document_requests == []


@pytest.mark.parametrize("episode", ["Episode I", "Episode II", "Episode III"])
def test_enemy_grid_sorted_filtered_click_uses_correct_row(page, live_url, episode):
    page.goto(live_url + "/xenosaga")
    page.get_by_role("tab", name=episode, exact=True).click()
    grid = page.locator("#xenosaga-grid")
    episode_id = {"Episode I": "ep1", "Episode II": "ep2", "Episode III": "ep3"}[episode]
    episode_rows = grid.locator(f".ag-row[row-id^='{episode_id}:']")
    expect(episode_rows.first).to_be_visible()
    cells = episode_rows.locator(".ag-cell[col-id='Name']")
    expect(cells.first).to_be_visible()
    grid.locator(".ag-header-cell[col-id='Name'] .ag-header-cell-label").click()
    grid.locator(".ag-header-cell[col-id='Name'] .ag-header-cell-label").click()
    expected = cells.first.inner_text()
    row_id = cells.first.locator("xpath=ancestor::div[@role='row']").get_attribute("row-id")
    page.evaluate("""async (name) => {
        const api = await dash_ag_grid.getApiAsync('xenosaga-grid');
        api.setFilterModel({Name: {filterType: 'text', type: 'equals', filter: name}});
    }""", expected)
    row = grid.locator(f".ag-row[row-id='{row_id}']")
    name_cell = row.locator(".ag-cell[col-id='Name']").first
    expect(name_cell).to_have_text(expected)
    name_cell.click()
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
    active_first_row = grid.locator(
        f".ag-row[row-id^='{character.lower()}:'][row-index='0']"
    )
    expect(active_first_row).to_be_visible()
    cell = active_first_row.locator(".ag-cell[col-id='Skill']")
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


def test_rybbit_calculator_and_xenosaga_events(page, live_url):
    page.route("**/analytics/script.js?*", lambda route: route.fulfill(content_type="application/javascript", body=""))
    page.route("https://plausible.automateordie.dev/**", lambda route: route.fulfill(content_type="application/javascript", body=""))
    page.add_init_script("""window.analyticsEvents = [];
        window.rybbit = {event: (name, props) => window.analyticsEvents.push({name, props})};""")
    page.goto(live_url + "/exp33/calculator")
    result = page.locator("#exp33-calculator-result-body")
    expect(result.get_by_role("heading", name="Lightning Dance", exact=True)).to_be_visible()
    assert page.evaluate("window.analyticsEvents") == []
    attack = page.locator("#exp33-calculator-attack")
    attack.fill("2000")
    attack.press("Tab")
    expect(result.get_by_role("heading", name="7,200", exact=True)).to_be_visible()
    page.wait_for_function("analyticsEvents.some(e => e.name === 'calculator_used')")
    attack.fill("1000")
    attack.press("Tab")
    expect(result.get_by_role("heading", name="3,600", exact=True)).to_be_visible()
    assert page.evaluate("analyticsEvents.filter(e => e.name === 'calculator_used').length") == 1
    page.locator("#exp33-calculator-save-upload input[type=file]").set_input_files({
        "name": "private-name.sav", "mimeType": "application/octet-stream", "buffer": b"invalid",
    })
    page.wait_for_function("analyticsEvents.some(e => e.name === 'save_import_failed')")
    assert "private-name" not in str(page.evaluate("analyticsEvents"))
    # Exercise the successful response contract without uploading a real save.
    page.evaluate("""dash_clientside.set_props('exp33-calculator-save-import-status', {
        children: 'Imported a save.', color: 'info', is_open: true
    })""")
    page.wait_for_function("analyticsEvents.some(e => e.name === 'save_import_succeeded')")

    page.goto(live_url + "/xenosaga")
    grid = page.locator("#xenosaga-grid")
    expect(grid.locator(".ag-row").first).to_be_visible()
    assert page.evaluate("analyticsEvents") == []
    page.get_by_role("tab", name="Episode II", exact=True).click()
    page.wait_for_function("analyticsEvents.some(e => e.name === 'xenosaga_episode_selected')")
    expect(grid.locator(".ag-row[row-id^='ep2:']").first).to_be_visible()
    grid.locator(".ag-cell[col-id='Name']").first.click()
    page.wait_for_function("analyticsEvents.some(e => e.name === 'xenosaga_enemy_details_opened')")
    page.locator("#xenosaga-close").click()
    page.evaluate("""async () => {
        const api = await dash_ag_grid.getApiAsync('xenosaga-grid');
        api.setFilterModel({Name: {filterType: 'text', type: 'contains', filter: 'a'}});
    }""")
    page.wait_for_function("analyticsEvents.some(e => e.name === 'xenosaga_table_filtered')")
    # An unavailable tracker must not break the interaction callback.
    page.evaluate("""() => {
        delete window.rybbit;
        dash_clientside.analytics.saveImport(null, 'danger', true);
    }""")


def test_xenosaga_is_readable_without_javascript(browser, live_url):
    context = browser.new_context(java_script_enabled=False)
    try:
        page = context.new_page()
        response = page.goto(live_url)
        assert response.status == 200
        page.get_by_role("link", name="Xenosaga Enemy Database", exact=False).click()
        expect(page).to_have_url(f"{live_url}/xenosaga")
        expect(page.get_by_role("heading", name="Xenosaga Enemy Database", exact=True)).to_be_visible()
        expect(page.get_by_role("table")).to_have_count(3)
        expect(page.locator("th[scope='row']")).to_have_count(325)
        assert page.get_by_role("link", name="Markdown edition").get_attribute("href") == "/xenosaga.md"
    finally:
        context.close()


@pytest.mark.parametrize("reduced_motion", ["no-preference", "reduce"])
def test_navigation_and_enemy_dialog_respect_motion_preference(page, live_url, reduced_motion):
    page.emulate_media(reduced_motion=reduced_motion)
    page.add_init_script("""
        const startTransition = document.startViewTransition.bind(document);
        window.completedPageTransitions = 0;
        document.startViewTransition = update => {
            const transition = startTransition(update);
            transition.ready.then(() => window.completedPageTransitions++, () => {});
            return transition;
        };
    """)
    page.goto(live_url)
    page.get_by_text("Enemy Database", exact=True).click()
    expect(page).to_have_url(f"{live_url}/xenosaga")
    cell = page.locator("#xenosaga-grid .ag-cell[col-id='Name']").first
    expect(cell).to_be_visible()
    if reduced_motion == "no-preference":
        page.wait_for_function("window.completedPageTransitions === 1")
    else:
        assert page.evaluate("window.completedPageTransitions") == 0

    cell.click()
    dialog = page.locator(".xenosaga-enemy-dialog .modal-dialog")
    expect(dialog).to_be_visible()
    expect(dialog).to_have_css(
        "transition-duration", "0s" if reduced_motion == "reduce" else "0.16s"
    )
