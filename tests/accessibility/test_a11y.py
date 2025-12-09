import pytest
from axe_playwright_python.sync_playwright import Axe
from playwright.sync_api import Page


@pytest.mark.django_db
def test_accessibility_login(live_server, page: Page):
    """
    Runs Axe-Core accessibility checks against the login page.
    """
    # Check if static files are serving
    try:
        response = page.goto(f"{live_server.url}/static/css/cedrus-ui.css")
        if response.status != 200:
            print(f"WARNING: Failed to load CSS. Status: {response.status}")
    except Exception as e:
        print(f"WARNING: Exception loading CSS: {e}")

    page.goto(live_server.url)

    # Inject axe-core and run
    results = Axe().run(page)

    # Filter for violations
    violations = results.response.get("violations", [])

    if violations:
        report = []
        for v in violations:
            report.append(f"Impact: {v['impact']}")
            report.append(f"Description: {v['description']}")
            report.append(f"Help: {v['help']}")
            report.append(f"Nodes: {len(v['nodes'])}")
            report.append("-" * 40)

        error_msg = "\n".join(report)
        pytest.fail(f"Accessibility Violations Found:\n{error_msg}")

    if violations:
        report = []
        for v in violations:
            report.append(f"Impact: {v.impact}")
            report.append(f"Description: {v.description}")
            report.append(f"Help: {v.help}")
            report.append(f"Nodes: {len(v.nodes)}")
            report.append("-" * 40)

        error_msg = "\n".join(report)
        pytest.fail(f"Accessibility Violations Found:\n{error_msg}")
