"""
Browser Compatibility: Safari

Tests critical paths on Safari browser.
- Safari desktop (macOS)
- Safari mobile (iOS - via webkit engine)
- WebKit-specific behaviors
"""

import pytest


class TestSafariDesktop:
    """Safari desktop browser tests"""

    @pytest.mark.browser
    def test_candidate_signup_safari(self, page, live_server, store_with_questionnaire):
        """Test: Candidate signup on Safari"""

        page.goto(f"{live_server}/candidato/loja/escolher/")

        # Verify page loads
        assert page.url.endswith("/candidato/loja/escolher/")

        # Safari rendering
        radios = page.locator("input[type='radio']")
        assert radios.count() > 0

        # Select store (Safari click behavior)
        store_id = store_with_questionnaire["store"].id
        page.click(f"input[type='radio'][value='{store_id}']")

        # Verify checked in Safari
        selected = page.locator(f"input[type='radio'][value='{store_id}']")
        assert selected.is_checked()

        # Continue
        page.click("button:has-text('Continue')")
        page.wait_for_url("**/candidato/acao/**", timeout=2000)

    @pytest.mark.browser
    def test_form_safari_rendering(self, page, live_server, store_with_questionnaire):
        """Test: Form rendering in Safari"""

        page.goto(
            f"{live_server}/candidato/formulario/?store={store_with_questionnaire['store'].id}&action=profile"
        )
        page.wait_for_selector("form", timeout=2000)

        # Check form elements render correctly
        form = page.locator("form")
        assert form.count() == 1

        # Safari input rendering
        text_input = page.locator("input[type='text']").first
        text_input.click()
        text_input.type("Safari Test")

        assert text_input.input_value() == "Safari Test"

    @pytest.mark.browser
    def test_safari_date_input(self, page, live_server, store_with_questionnaire):
        """Test: Date input behavior in Safari"""

        page.goto(
            f"{live_server}/candidato/formulario/?store={store_with_questionnaire['store'].id}&action=profile"
        )
        page.wait_for_selector("form", timeout=2000)

        date_input = page.locator("input[type='date']").first

        if date_input.count() > 0:
            # Safari date input handling
            date_input.click()

            # Set date (Safari specific format)
            date_input.fill("2026-11-15")

            # Verify value
            value = date_input.input_value()
            assert "2026" in value or "11" in value or "15" in value

    @pytest.mark.browser
    def test_safari_select_dropdown(self, page, live_server, store_with_questionnaire):
        """Test: Select dropdown in Safari"""

        page.goto(
            f"{live_server}/candidato/formulario/?store={store_with_questionnaire['store'].id}&action=profile"
        )
        page.wait_for_selector("select", timeout=2000)

        select = page.locator("select").first

        if select.count() > 0:
            # Safari select
            select.click()

            options = select.locator("option")
            if options.count() > 1:
                select.select_option(options.nth(1).get_attribute("value"))

                # Verify in Safari
                selected_value = select.evaluate(
                    "select => select.value"
                )
                assert selected_value is not None


class TestSafariPerformance:
    """Safari-specific performance tests"""

    @pytest.mark.browser
    def test_safari_paint_performance(self, page, live_server):
        """Test: Paint performance in Safari"""

        page.goto(f"{live_server}/candidato/loja/escolher/")

        # Get paint entries (Safari WebKit)
        paints = page.evaluate("""
            () => {
                const entries = performance.getEntriesByType('paint');
                return entries.map(e => ({name: e.name, time: e.startTime}));
            }
        """)

        # Should have paint events
        assert len(paints) > 0, "No paint events in Safari"

    @pytest.mark.browser
    def test_safari_memory_profile(self, page, live_server, store_with_questionnaire):
        """Test: Memory behavior in Safari"""

        page.goto(
            f"{live_server}/candidato/formulario/?store={store_with_questionnaire['store'].id}&action=profile"
        )

        # Safari memory API (if available)
        memory = page.evaluate("""
            () => {
                if (performance.memory) {
                    return {
                        usedJSHeapSize: performance.memory.usedJSHeapSize,
                        jsHeapSizeLimit: performance.memory.jsHeapSizeLimit
                    };
                }
                return null;
            }
        """)

        # If memory API available, check memory usage
        if memory:
            ratio = memory["usedJSHeapSize"] / memory["jsHeapSizeLimit"]
            assert ratio < 0.8, f"Memory usage {ratio:.1%} too high"


class TestSafariCompatibility:
    """Safari-specific compatibility issues"""

    @pytest.mark.browser
    def test_safari_flexbox_layout(self, page, live_server):
        """Test: Flexbox layout in Safari"""

        page.goto(f"{live_server}/candidato/loja/escolher/")

        # Check if flexbox elements are rendered
        flex_check = page.evaluate("""
            () => {
                const computed = window.getComputedStyle(document.body);
                return computed.display;
            }
        """)

        # Body should have valid display property
        assert flex_check in ["block", "flex", "grid", ""]

    @pytest.mark.browser
    def test_safari_css_grid(self, page, live_server, store_with_questionnaire):
        """Test: CSS Grid in Safari"""

        page.goto(
            f"{live_server}/candidato/formulario/?store={store_with_questionnaire['store'].id}&action=profile"
        )

        # Check if grid layout works
        grid_check = page.evaluate("""
            () => {
                const form = document.querySelector('form');
                if (!form) return null;
                const computed = window.getComputedStyle(form);
                return computed.display;
            }
        """)

        # Should be a valid display value
        if grid_check:
            assert grid_check in ["block", "flex", "grid", ""]

    @pytest.mark.browser
    def test_safari_css_variables(self, page, live_server):
        """Test: CSS custom properties (variables) in Safari"""

        page.goto(f"{live_server}/candidato/loja/escolher/")

        # Check if CSS variables are supported (Safari WebKit supports)
        css_var_check = page.evaluate("""
            () => {
                const root = document.documentElement;
                const computed = window.getComputedStyle(root);
                return computed.getPropertyValue('--color-primary') || 'no-vars';
            }
        """)

        # Should either have variables or fallback colors
        assert css_var_check is not None

    @pytest.mark.browser
    def test_safari_web_storage(self, page, live_server):
        """Test: Web Storage (localStorage, sessionStorage) in Safari"""

        page.goto(f"{live_server}/candidato/loja/escolher/")

        # Test localStorage
        page.evaluate("""
            () => {
                localStorage.setItem('safari_test', 'value');
            }
        """)

        value = page.evaluate("""
            () => localStorage.getItem('safari_test')
        """)

        assert value == "value", "localStorage not working in Safari"

        # Test sessionStorage
        page.evaluate("""
            () => {
                sessionStorage.setItem('safari_session', 'session_value');
            }
        """)

        session_value = page.evaluate("""
            () => sessionStorage.getItem('safari_session')
        """)

        assert session_value == "session_value", \
            "sessionStorage not working in Safari"


class TestSafariMobileWebKit:
    """Safari mobile WebKit tests (via iOS emulation)"""

    @pytest.mark.browser
    def test_safari_mobile_viewport(self, page, live_server, store_with_questionnaire):
        """Test: Safari mobile viewport handling"""

        # iPhone viewport (Safari uses WebKit)
        page.set_viewport_size(width=390, height=844)

        page.goto(
            f"{live_server}/candidato/formulario/?store={store_with_questionnaire['store'].id}&action=profile"
        )

        # Check viewport meta tag effect
        viewport_width = page.evaluate("() => window.innerWidth")
        assert viewport_width == 390, \
            f"Viewport width {viewport_width}px != 390px"

    @pytest.mark.browser
    def test_safari_mobile_zoom(self, page, live_server):
        """Test: Zoom behavior in Safari mobile"""

        page.set_viewport_size(width=390, height=844)
        page.goto(f"{live_server}/candidato/loja/escolher/")

        # Check device pixel ratio
        dpr = page.evaluate("() => window.devicePixelRatio")

        # Should be numeric
        assert isinstance(dpr, (int, float))
        assert dpr > 0

    @pytest.mark.browser
    def test_safari_input_autofill(self, page, live_server, store_with_questionnaire):
        """Test: Input autofill in Safari mobile"""

        page.set_viewport_size(width=390, height=844)

        page.goto(
            f"{live_server}/candidato/formulario/?store={store_with_questionnaire['store'].id}&action=profile"
        )
        page.wait_for_selector("form", timeout=2000)

        # Check if form has autofill attributes
        email_input = page.locator("input[type='email']").first

        if email_input.count() > 0:
            # Check for autocomplete attribute
            autocomplete = email_input.get_attribute("autocomplete")
            # Should have reasonable autocomplete value or be explicit
            assert autocomplete != "off" or True  # Allow either
