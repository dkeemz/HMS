"""E2E tests verifying responsive layout at different viewport widths."""

from __future__ import annotations

from playwright.sync_api import Page, expect


def test_desktop_layout(page: Page) -> None:
    """At 1280px+ the sidebar is visible and main content has left margin."""
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


def test_tablet_layout(page: Page) -> None:
    """At 768px the hamburger menu is visible (sidebar hidden on smaller screens)."""
    page.set_viewport_size({"width": 768, "height": 1024})
    page.goto("/")
    page.wait_for_timeout(500)

    hamburger = page.locator("button[aria-label='Open navigation menu']")
    expect(hamburger).to_be_visible()


def test_mobile_layout(page: Page) -> None:
    """At 375px the sidebar is off-screen and the hamburger opens it as a drawer."""
    page.set_viewport_size({"width": 375, "height": 812})
    page.goto("/")
    page.wait_for_timeout(500)

    hamburger = page.locator("button[aria-label='Open navigation menu']")
    expect(hamburger).to_be_visible()

    # Sidebar overlay should exist but be hidden initially
    overlay = page.locator("#sidebar-overlay")
    expect(overlay).to_be_attached()


def test_desktop_search_visible(page: Page) -> None:
    """The global search bar is visible on desktop but hidden on mobile."""
    page.set_viewport_size({"width": 1280, "height": 720})
    page.goto("/")

    search_wrapper = page.locator("#global-search-wrapper")
    expect(search_wrapper).to_be_visible()


def test_mobile_search_hidden(page: Page) -> None:
    """The global search bar is hidden on mobile viewports."""
    page.set_viewport_size({"width": 375, "height": 812})
    page.goto("/")
    page.wait_for_timeout(500)

    search_wrapper = page.locator("#global-search-wrapper")
    expect(search_wrapper).to_be_hidden()
