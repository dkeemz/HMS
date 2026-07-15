"""E2E tests for the admin dashboard pages."""

from __future__ import annotations

from playwright.sync_api import Page, expect

# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

def test_dashboard_loads_with_stats(page: Page) -> None:
    """The root dashboard page renders stats cards and quick actions."""
    page.goto("/")

    expect(page).to_have_title("Dashboard — HMS")
    expect(page.locator("#stat-total-users")).to_be_visible()
    expect(page.locator("#stat-active-sessions")).to_be_visible()
    expect(page.locator("#stat-recent-logins")).to_be_visible()
    expect(page.locator("#stat-security-alerts")).to_be_visible()

    # Quick action links
    expect(page.locator("text=Add Patient")).to_be_visible()
    expect(page.locator("text=Audit Log")).to_be_visible()


# ---------------------------------------------------------------------------
# User management
# ---------------------------------------------------------------------------

def test_user_management_page_loads(page: Page) -> None:
    """Admin users page loads with table and filter controls."""
    page.goto("/admin/users")

    expect(page).to_have_title("User Management — HMS")
    expect(page.locator("#search-users")).to_be_visible()
    expect(page.locator("#filter-role")).to_be_visible()
    expect(page.locator("#filter-status")).to_be_visible()


def test_user_list_pagination_visible(page: Page) -> None:
    """The user management page includes a pagination container."""
    page.goto("/admin/users")
    expect(page.locator("#users-pagination")).to_be_attached()


def test_create_user_flow(page: Page) -> None:
    """Opening the create-user modal shows the expected form fields."""
    page.goto("/admin/users")
    page.click("text=Add User")

    modal = page.locator("#create-user-modal")
    expect(modal).to_be_visible()
    expect(page.locator("#create-first-name")).to_be_visible()
    expect(page.locator("#create-last-name")).to_be_visible()
    expect(page.locator("#create-email")).to_be_visible()
    expect(page.locator("#create-role")).to_be_visible()
    expect(page.locator("#create-password")).to_be_visible()


# ---------------------------------------------------------------------------
# Roles
# ---------------------------------------------------------------------------

def test_roles_page_loads(page: Page) -> None:
    """Role management page renders with tabs."""
    page.goto("/admin/roles")
    expect(page).to_have_title("Role Management — HMS")
    expect(page.locator("#tab-roles")).to_be_visible()
    expect(page.locator("#tab-matrix")).to_be_visible()
    expect(page.locator("#tab-assignments")).to_be_visible()


def test_role_assignment_flow(page: Page) -> None:
    """Switching to the role assignments tab shows the assignment table."""
    page.goto("/admin/roles")
    page.click("#tab-assignments")
    expect(page.locator("#section-assignments")).to_be_visible()
    expect(page.locator("#assignments-table-body")).to_be_attached()


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------

def test_audit_log_page_loads(page: Page) -> None:
    """Audit log page loads with search and filter controls."""
    page.goto("/admin/audit")
    expect(page).to_have_title("Audit Log — HMS")
    expect(page.locator("#search-audit")).to_be_visible()
    expect(page.locator("#filter-event-type")).to_be_visible()


def test_audit_log_search(page: Page) -> None:
    """Typing into the audit search input fires an HTMX request."""
    page.goto("/admin/audit")
    page.fill("#search-audit", "login")
    # After typing, the HTMX request should trigger; verify the element exists
    expect(page.locator("#audit-table-body")).to_be_attached()


# ---------------------------------------------------------------------------
# Break Glass
# ---------------------------------------------------------------------------

def test_break_glass_page_loads(page: Page) -> None:
    """Break-glass request page renders."""
    page.goto("/admin/break-glass")
    expect(page).to_have_title("Break-Glass Admin Dashboard")
