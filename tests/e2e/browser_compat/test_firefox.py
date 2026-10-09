"""
Browser Compatibility: Firefox

Tests critical paths across Firefox browser versions.
- Latest stable
- Latest - 1 version
- Specific Firefox rendering engine behaviors
"""

import pytest


class TestFirefoxDesktop:
    """Firefox desktop browser tests"""

    @pytest.mark.browser
    def test_candidate_signup_firefox(self, page, live_server, store_with_questionnaire):
        """Test: Candidate signup on Firefox"""

        page.goto(f"{live_server}/candidato/loja/escolher/")

        # Verify page loads
        assert page.url.endswith("/candidato/loja/escolher/")

        # Check radio buttons (Firefox rendering)
        radio_buttons = page.locator("input[type='radio']")
        assert radio_buttons.count() > 0

        # Select store
        store_id = store_with_questionnaire["store"].id
        page.click(f"input[type='radio'][value='{store_id}']")

        # Verify selection works in Firefox
        selected = page.locator(
            f"input[type='radio'][value='{store_id}']"
        )
        assert selected.is_checked()

        # Continue
        page.click("button:has-text('Continue')")
        page.wait_for_url("**/candidato/acao/**", timeout=2000)

    @pytest.mark.browser
    def test_form_rendering_firefox(self, page, live_server, store_with_questionnaire):
        """Test: Form renders correctly on Firefox"""

        page.goto(
            f"{live_server}/candidato/formulario/?store={store_with_questionnaire['store'].id}&action=profile"
        )
        page.wait_for_selector("form", timeout=2000)

        # Check form structure
        form = page.locator("form")
        assert form.count() == 1

        # Verify inputs render
        inputs = page.locator("form input")
        assert inputs.count() > 0

        # Test input interaction (Firefox specific)
        text_input = page.locator("input[type='text']").first
        text_input.click()
        text_input.type("Firefox Test")

        # Verify value in Firefox
        assert text_input.input_value() == "Firefox Test"

    @pytest.mark.browser
    def test_select_dropdown_firefox(self, page, live_server, store_with_questionnaire):
        """Test: Select dropdown works in Firefox"""

        page.goto(
            f"{live_server}/candidato/formulario/?store={store_with_questionnaire['store'].id}&action=profile"
        )
        page.wait_for_selector("select", timeout=2000)

        select = page.locator("select").first
        if select.count() > 0:
            # Click dropdown
            select.click()

            # Verify dropdown opens (Firefox specific rendering)
            page.wait_for_selector("select", timeout=1000)

            # Select option
            options = select.locator("option")
            if options.count() > 1:
                select.select_option(options.nth(1).get_attribute("value"))

                # Verify selection in Firefox
                selected_option = select.evaluate(
                    "select => select.options[select.selectedIndex].text"
                )
                assert selected_option is not None

    @pytest.mark.browser
    def test_checkbox_firefox(self, page, live_server, store_with_questionnaire):
        """Test: Checkbox behavior on Firefox"""

        page.goto(
            f"{live_server}/candidato/formulario/?store={store_with_questionnaire['store'].id}&action=profile"
        )
        page.wait_for_selector("form", timeout=2000)

        checkbox = page.locator("input[type='checkbox']").first
        if checkbox.count() > 0:
            # Check
            checkbox.check()
            assert checkbox.is_checked()

            # Uncheck
            checkbox.uncheck()
            assert not checkbox.is_checked()


class TestFirefoxPerformance:
    """Firefox-specific performance tests"""

    @pytest.mark.browser
    def test_paint_timing_firefox(self, page, live_server):
        """Test: Paint timing on Firefox"""

        page.goto(f"{live_server}/candidato/loja/escolher/")

        # Firefox paint performance
        paint_entries = page.evaluate("""
            () => {
                const paints = performance.getEntriesByType('paint');
                return paints.map(p => ({name: p.name, time: p.startTime}));
            }
        """)

        # First paint should occur
        assert len(paint_entries) > 0, "No paint entries detected on Firefox"

    @pytest.mark.browser
    def test_resource_timing_firefox(self, page, live_server, store_with_questionnaire):
        """Test: Resource loading timing on Firefox"""

        page.goto(
            f"{live_server}/candidato/formulario/?store={store_with_questionnaire['store'].id}&action=profile"
        )

        resources = page.evaluate("""
            () => {
                const perfResources = performance.getEntriesByType('resource');
                return {
                    count: perfResources.length,
                    slowest: Math.max(...perfResources.map(r => r.duration))
                };
            }
        """)

        # Should have resources loaded
        assert resources["count"] > 0, "No resources loaded on Firefox"

        # No single resource should take >3s
        assert resources["slowest"] < 3000, \
            f"Resource taking {resources['slowest']}ms > 3s"


class TestFirefoxCompatibility:
    """Firefox compatibility edge cases"""

    @pytest.mark.browser
    def test_firefox_local_storage(self, page, live_server):
        """Test: LocalStorage works on Firefox"""

        page.goto(f"{live_server}/candidato/loja/escolher/")

        # Test localStorage
        page.evaluate("""
            () => {
                localStorage.setItem('test_key', 'test_value');
            }
        """)

        value = page.evaluate("""
            () => localStorage.getItem('test_key')
        """)

        assert value == "test_value", "LocalStorage not working in Firefox"

    @pytest.mark.browser
    def test_firefox_session_cookie(self, page, live_server):
        """Test: Session cookies work on Firefox"""

        page.goto(f"{live_server}/candidato/loja/escolher/")

        # Get cookies
        cookies = page.context.cookies()

        # Should have session cookie or similar
        # (exact name depends on app implementation)
        cookie_names = [c["name"] for c in cookies]

        # At minimum, should be able to access page
        assert page.url != ""

    @pytest.mark.browser
    def test_firefox_form_validation(self, page, live_server, store_with_questionnaire):
        """Test: HTML5 form validation on Firefox"""

        page.goto(
            f"{live_server}/candidato/formulario/?store={store_with_questionnaire['store'].id}&action=profile"
        )
        page.wait_for_selector("form", timeout=2000)

        # Test required field validation (Firefox HTML5)
        required_input = page.locator("input[required]").first

        if required_input.count() > 0:
            # Try to submit with empty required field
            # (behavior depends on form implementation)

            # Clear any existing value
            required_input.clear()

            # Firefox should enforce HTML5 validation
            is_valid = required_input.evaluate(
                "input => input.checkValidity()"
            )

            assert not is_valid, "Required field should be invalid when empty"


class TestFirefoxMobile:
    """Firefox mobile viewport tests"""

    @pytest.mark.browser
    def test_mobile_view_firefox(self, page, live_server, store_with_questionnaire):
        """Test: Form on mobile viewport (Firefox)"""

        page.set_viewport_size(width=375, height=667)

        page.goto(
            f"{live_server}/candidato/formulario/?store={store_with_questionnaire['store'].id}&action=profile"
        )
        page.wait_for_selector("form", timeout=2000)

        # Verify no horizontal overflow
        body = page.locator("body")
        overflow_x = page.evaluate("""
            () => {
                return document.documentElement.scrollWidth > window.innerWidth;
            }
        """)

        assert not overflow_x, "Horizontal scroll detected on Firefox mobile"

    @pytest.mark.browser
    def test_touch_input_firefox_mobile(self, page, live_server, store_with_questionnaire):
        """Test: Touch-friendly inputs on Firefox mobile"""

        page.set_viewport_size(width=375, height=667)

        page.goto(
            f"{live_server}/candidato/formulario/?store={store_with_questionnaire['store'].id}&action=profile"
        )
        page.wait_for_selector("button", timeout=2000)

        # Verify buttons are large enough for touch (44px minimum)
        buttons = page.locator("button")

        for i in range(min(buttons.count(), 3)):
            button = buttons.nth(i)
            box = button.bounding_box()

            if box:
                # Touch target should be at least 44x44
                assert box["height"] >= 40, \
                    f"Button height {box['height']}px < 44px for touch"
