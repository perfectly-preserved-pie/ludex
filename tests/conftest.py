from threading import Thread

import pytest

from app import app


def pytest_addoption(parser):
    parser.addoption("--run-browser", action="store_true", help="Run Chromium integration tests")


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-browser"):
        skip = pytest.mark.skip(reason="Use --run-browser after installing Playwright Chromium")
        for item in items:
            if "browser" in item.keywords:
                item.add_marker(skip)


@pytest.fixture(scope="session")
def dash_app():
    app.server.config["TESTING"] = True
    with app.server.test_client() as client:
        client.get("/")  # Register Dash's callbacks and page router once.
    return app


@pytest.fixture
def client(dash_app):
    return dash_app.server.test_client()


@pytest.fixture(scope="session")
def live_url(dash_app):
    from werkzeug.serving import make_server

    server = make_server("127.0.0.1", 0, dash_app.server, threaded=True)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    thread.join(timeout=5)
    server.server_close()


@pytest.fixture(scope="session")
def browser():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        yield browser
        browser.close()


@pytest.fixture
def page(browser):
    context = browser.new_context(viewport={"width": 1440, "height": 1000})
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    yield page
    context.close()
    assert not errors, "Browser errors: " + "\n".join(errors)
