import pytest
from playwright.sync_api import Page
from axe_playwright_python.sync_playwright import Axe

@pytest.mark.django_db
def test_accessibility_login(live_server, page: Page):
    """
    Runs Axe-Core accessibility checks against the login page.
    """
    page.goto(live_server.url)
    
    # Inject axe-core and run
    results = Axe().run(page)
    
    # Filter for violations
    violations = results.get("violations", [])
    
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
