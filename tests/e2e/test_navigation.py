"""E2E tests for navigation elements and responsive layouts."""

from __future__ import annotations

import re

from playwright.sync_api import Page, expect

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def test_sidebar_links(page: Page) -> None:
    """Sidebar is visible on desktop with all expected nav links."""
    page.set_viewport_size({"width": 1280, "height": 720})
    page.goto("/")

    sidebar = page.locator("#app-sidebar")
    expect(sidebar).to_be_visible()

    expect(sidebar.locator("text=Dashboard")).to_be_visible()
    expect(sidebar.locator("text=Patients")).to_be_visible()
    expect(sidebar.locator("text=Appointments")).to_be_visible()
    expect(sidebar.locator("text=Records")).to_be_visible()
    expect(sidebar.locator("text=Audit Log")).to_be_visible()
    expect(sidebar.locator("text=Break Glass")).to_be_visible()


def test_sidebar_collapse_toggle(page: Page) -> None:
    """Clicking the collapse button adds 'collapsed' class to sidebar."""
    page.set_viewport_size({"width": 1280, "height": 720})
    page.goto("/")
    page.wait_for_selector("#app-sidebar")

    collapse_btn = page.locator("button[aria-label='Toggle sidebar']")
    expect(collapse_btn).to_be_visible()
    collapse_btn.click()

    sidebar = page.locator("#app-sidebar")
    expect(sidebar).to_have_class(re.compile(r"collapsed"))


# ---------------------------------------------------------------------------
# Header elements
# ---------------------------------------------------------------------------

def test_header_elements(page: Page) -> None:
    """Header contains search, notifications, theme toggle, and user menu."""
    page.goto("/")

    expect(page.locator("#global-search")).to_be_visible()
    expect(page.locator("button[aria-label='Notifications']")).to_be_visible()
    expect(page.locator("button[aria-label='Toggle dark mode']")).to_be_visible()
    expect(page.locator("button[aria-label='User menu']")).to_be_visible()


def test_dark_mode_toggle(page: Page) -> None:
    """Clicking the theme toggle switches between light and dark mode."""
    page.goto("/")

    theme_btn = page.locator("button[aria-label='Toggle dark mode']")
    expect(theme_btn).to_be_visible()

    html_classes = page.locator("html").get_attribute("class") or ""
    was_dark = "dark" in html_classes

    theme_btn.click()
    page.wait_for_timeout(300)

    html_classes_after = page.locator("html").get_attribute("class") or ""
    is_dark = "dark" in html_classes_after

    assert is_dark != was_dark, "Dark mode did not toggle"


def test_user_menu_opens(page: Page) -> None:
    """Clicking the user avatar opens the user menu dropdown."""
    page.goto("/")

    menu_btn = page.locator("button[aria-label='User menu']")
    expect(menu_btn).to_be_visible()
    menu_btn.click()

    panel = page.locator("#user-menu-panel")
    expect(panel).to_be_visible()
    expect(panel.locator("text=Profile")).to_be_visible()
    expect(panel.locator("text=Settings")).to_be_visible()
    expect(panel.locator("text=Sign out")).to_be_visible()


# ---------------------------------------------------------------------------
# Mobile responsive
# ---------------------------------------------------------------------------

def test_responsive_mobile(page: Page) -> None:
    """On mobile (< 768px) the sidebar is hidden and a hamburger button opens it."""
    page.set_viewport_size({"width": 375, "height": 812})
    page.goto("/")
    page.wait_for_timeout(500)

    hamburger = page.locator("button[aria-label='Open navigation menu']")
    expect(hamburger).to_be_visible()

    # Sidebar overlay should exist but be hidden initially
    overlay = page.locator("#sidebar-overlay")
    expect(overlay).to_be_attached()

    # Open drawer
    hamburger.click()
    sidebar = page.locator("#app-sidebar")
    expect(sidebar).to_be_visible()


# ---------------------------------------------------------------------------
# Tablet responsive
# ---------------------------------------------------------------------------

def test_responsive_tablet(page: Page) -> None:
    """At 768px the hamburger menu is visible (sidebar hidden)."""
    page.set_viewport_size({"width": 768, "height": 1024})
    page.goto("/")
    page.wait_for_timeout(500)

    hamburger = page.locator("button[aria-label='Open navigation menu']")
    expect(hamburger).to_be_visible()


# ---------------------------------------------------------------------------
# Desktop responsive
# ---------------------------------------------------------------------------

def test_responsive_desktop(page: Page) -> None:
    """At 1280px the sidebar is visible and main content has left margin."""
    page.set_viewport_size({"width": 1280, "height": 720})
    page.goto("/")

    sidebar = page.locator("#app-sidebar")
    expect(sidebar).to_be_visible()

    # The main layout area should have a left margin to accommodate the sidebar
    main_area = page.locator("#main-layout-area")
    margin_left = main_area.evaluate(
        "el => getComputedStyle(el).marginLeft"
    )
    assert margin_left != "0px", (
        f"Expected non-zero margin on desktop, got {margin_left}"
    )
