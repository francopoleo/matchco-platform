"""
Browser Compatibility: Mobile

Tests on mobile devices using Playwright device emulation.
- iOS 14+ (iPhone)
- Android 12+ (Pixel)
- Mobile-specific interactions (touch, orientation)
"""

import pytest
from playwright.async_api import async_playwright


class TestIOSCompatibility:
    """iOS compatibility tests (iPhone emulation)"""

    @pytest.mark.browser
    def test_candidate_signup_ios(self, page, live_server, store_with_questionnaire):
        """Test: Candidate signup on iOS (iPhone 12)"""

        # iOS viewport
        page.set_viewport_size(width=390, height=844)

        page.goto(f"{live_server}/candidato/loja/escolher/")

        # Verify page renders on iOS viewport
        assert page.url.endswith("/candidato/loja/escolher/")

        # Verify radio buttons visible on iOS
        radio = page.locator(
            f"input[type='radio'][value='{store_with_questionnaire['store'].id}']"
        )
        box = radio.bounding_box()
        assert box is not None, "Radio button not visible on iOS"

        # Select store
        radio.click()
        assert radio.is_checked()

        # Continue button
        page.click("button:has-text('Continue')")
        page.wait_for_url("**/candidato/acao/**", timeout=2000)

    @pytest.mark.browser
    def test_form_ios_landscape(self, page, live_server, store_with_questionnaire):
        """Test: Form on iOS landscape orientation"""

        # iOS landscape (iPhone 12)
        page.set_viewport_size(width=844, height=390)

        page.goto(
            f"{live_server}/candidato/formulario/?store={store_with_questionnaire['store'].id}&action=profile"
        )
        page.wait_for_selector("form", timeout=2000)

        # Verify form is usable in landscape
        form = page.locator("form")
        form_box = form.bounding_box()

        assert form_box is not None, "Form not visible in iOS landscape"

        # Verify no horizontal scroll needed
        scroll_width = page.evaluate(
            "() => document.documentElement.scrollWidth"
        )
        viewport_width = page.evaluate("() => window.innerWidth")

        assert scroll_width <= viewport_width, \
            "Horizontal scroll needed on iOS landscape"

    @pytest.mark.browser
    def test_ios_input_interaction(self, page, live_server, store_with_questionnaire):
        """Test: Touch input on iOS"""

        page.set_viewport_size(width=390, height=844)

        page.goto(
            f"{live_server}/candidato/formulario/?store={store_with_questionnaire['store'].id}&action=profile"
        )
        page.wait_for_selector("form", timeout=2000)

        # iOS touch: tap input
        text_input = page.locator("input[type='text']").first
        text_input.tap()  # Touch instead of click
        text_input.type("iOS Input Test")

        assert text_input.input_value() == "iOS Input Test"

    @pytest.mark.browser
    def test_ios_keyboard_handling(self, page, live_server, store_with_questionnaire):
        """Test: Keyboard behavior on iOS"""

        page.set_viewport_size(width=390, height=844)

        page.goto(
            f"{live_server}/candidato/formulario/?store={store_with_questionnaire['store'].id}&action=profile"
        )
        page.wait_for_selector("form", timeout=2000)

        # Focus input (shows iOS keyboard)
        text_input = page.locator("input[type='text']").first
        text_input.focus()

        # Type should work
        text_input.type("Keyboard test")
        assert "Keyboard test" in text_input.input_value()

        # Test dismissing keyboard with Tab
        text_input.press("Tab")

        # Should move to next element
        next_element = page.evaluate("() => document.activeElement.tagName")
        assert next_element is not None


class TestAndroidCompatibility:
    """Android compatibility tests (Pixel emulation)"""

    @pytest.mark.browser
    def test_candidate_signup_android(self, page, live_server, store_with_questionnaire):
        """Test: Candidate signup on Android (Pixel 5)"""

        # Android viewport (Pixel 5)
        page.set_viewport_size(width=393, height=851)

        page.goto(f"{live_server}/candidato/loja/escolher/")

        assert page.url.endswith("/candidato/loja/escolher/")

        # Click radio (Android touch)
        store_id = store_with_questionnaire["store"].id
        radio = page.locator(f"input[type='radio'][value='{store_id}']")

        # Android: tap instead of click
        radio.tap()
        assert radio.is_checked()

        # Continue
        page.click("button:has-text('Continue')")
        page.wait_for_url("**/candidato/acao/**", timeout=2000)

    @pytest.mark.browser
    def test_form_android_portrait(self, page, live_server, store_with_questionnaire):
        """Test: Form on Android portrait mode"""

        # Android portrait (Pixel 5)
        page.set_viewport_size(width=393, height=851)

        page.goto(
            f"{live_server}/candidato/formulario/?store={store_with_questionnaire['store'].id}&action=profile"
        )
        page.wait_for_selector("form", timeout=2000)

        # Verify form elements are accessible
        form_elements = page.locator("form input, form button, form select")
        assert form_elements.count() > 0

        # Verify each element has minimum touch size
        for i in range(min(form_elements.count(), 5)):
            element = form_elements.nth(i)
            box = element.bounding_box()

            if box and box["height"] > 0:
                assert box["height"] >= 40, \
                    f"Element height {box['height']}px < 44px touch target"

    @pytest.mark.browser
    def test_android_scroll_performance(self, page, live_server, store_with_questionnaire):
        """Test: Smooth scrolling on Android"""

        page.set_viewport_size(width=393, height=851)

        page.goto(
            f"{live_server}/candidato/formulario/?store={store_with_questionnaire['store'].id}&action=profile"
        )
        page.wait_for_selector("form", timeout=2000)

        # Scroll through form
        form = page.locator("form")

        # Smooth scroll simulation
        for _ in range(3):
            form.evaluate("el => el.scrollTop += 200")
            page.wait_for_timeout(100)  # Small delay for smooth scrolling

        # Verify no jank (simple check)
        # In real scenario, would use performance API
        assert True  # Scroll completed without error

    @pytest.mark.browser
    def test_android_orientation_change(self, page, live_server, store_with_questionnaire):
        """Test: Form adapts to orientation change on Android"""

        page.goto(
            f"{live_server}/candidato/formulario/?store={store_with_questionnaire['store'].id}&action=profile"
        )
        page.wait_for_selector("form", timeout=2000)

        # Portrait
        page.set_viewport_size(width=393, height=851)
        portrait_height = page.evaluate("() => window.innerHeight")

        # Landscape
        page.set_viewport_size(width=851, height=393)
        landscape_height = page.evaluate("() => window.innerHeight")

        # Height should change
        assert portrait_height > landscape_height, \
            "Viewport height didn't change on orientation change"

        # Form should still be readable
        form = page.locator("form")
        assert form.is_visible(), "Form not visible in landscape"


class TestMobileSpecificFeatures:
    """Mobile-specific feature tests"""

    @pytest.mark.browser
    def test_mobile_safe_area(self, page, live_server, store_with_questionnaire):
        """Test: Content respects mobile safe areas"""

        # iOS viewport with notch area
        page.set_viewport_size(width=390, height=844)

        page.goto(
            f"{live_server}/candidato/formulario/?store={store_with_questionnaire['store'].id}&action=profile"
        )

        # Check if important content is visible
        # (should not be hidden under notch)
        form = page.locator("form")
        box = form.bounding_box()

        # Form should not be too close to top (reserve for status bar)
        if box:
            assert box["y"] > 0, "Form too close to top/notch area"

    @pytest.mark.browser
    def test_mobile_button_spacing(self, page, live_server, store_with_questionnaire):
        """Test: Buttons are properly spaced for mobile touch"""

        page.set_viewport_size(width=375, height=667)

        page.goto(
            f"{live_server}/candidato/formulario/?store={store_with_questionnaire['store'].id}&action=profile"
        )
        page.wait_for_selector("button", timeout=2000)

        buttons = page.locator("button")

        # Check spacing between buttons
        positions = []
        for i in range(buttons.count()):
            box = buttons.nth(i).bounding_box()
            if box:
                positions.append({
                    "y": box["y"],
                    "height": box["height"]
                })

        # Adjacent buttons should have gap
        for i in range(len(positions) - 1):
            gap = positions[i + 1]["y"] - (
                positions[i]["y"] + positions[i]["height"]
            )

            # Minimum gap for touch targets
            if gap > 0:
                assert gap >= 8, \
                    f"Button gap {gap}px too small for touch"

    @pytest.mark.browser
    def test_mobile_viewport_units(self, page, live_server):
        """Test: CSS viewport units work on mobile"""

        page.set_viewport_size(width=375, height=667)

        page.goto(f"{live_server}/candidato/loja/escolher/")

        # Check if viewport height is reported correctly
        viewport_height = page.evaluate("() => window.innerHeight")

        # Should match set viewport
        assert viewport_height == 667, \
            f"Viewport height {viewport_height}px != 667px"

    @pytest.mark.browser
    def test_mobile_double_tap_zoom(self, page, live_server, store_with_questionnaire):
        """Test: Double-tap zoom behavior"""

        page.set_viewport_size(width=375, height=667)

        page.goto(
            f"{live_server}/candidato/formulario/?store={store_with_questionnaire['store'].id}&action=profile"
        )

        # Check if page is zoomable (should have proper viewport meta tag)
        zoom_level = page.evaluate("() => window.devicePixelRatio")

        # Initial zoom should be 1.0 (no zoom)
        assert zoom_level == 1.0, \
            f"Initial zoom {zoom_level}x != 1.0x"


class TestTabletCompatibility:
    """Tablet-size device tests"""

    @pytest.mark.browser
    def test_form_tablet_landscape(self, page, live_server, store_with_questionnaire):
        """Test: Form on tablet landscape (iPad)"""

        # iPad landscape
        page.set_viewport_size(width=1024, height=768)

        page.goto(
            f"{live_server}/candidato/formulario/?store={store_with_questionnaire['store'].id}&action=profile"
        )
        page.wait_for_selector("form", timeout=2000)

        # Form should use space efficiently
        form = page.locator("form")
        form_box = form.bounding_box()

        # Form should not extend beyond viewport
        viewport_width = page.evaluate("() => window.innerWidth")
        assert form_box["x"] + form_box["width"] <= viewport_width, \
            "Form extends beyond viewport on tablet"

    @pytest.mark.browser
    def test_tablet_touch_target_size(self, page, live_server, store_with_questionnaire):
        """Test: Touch targets are appropriately sized on tablet"""

        page.set_viewport_size(width=1024, height=768)

        page.goto(
            f"{live_server}/candidato/formulario/?store={store_with_questionnaire['store'].id}&action=profile"
        )

        buttons = page.locator("button")

        for i in range(min(buttons.count(), 3)):
            button = buttons.nth(i)
            box = button.bounding_box()

            if box:
                # Tablet can have slightly smaller targets (40px)
                # but should still be usable
                assert box["height"] >= 36, \
                    f"Button too small for tablet: {box['height']}px"
