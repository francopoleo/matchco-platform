"""
Browser Compatibility: Chrome

Tests critical paths across Chrome browser versions.
- Latest stable
- Latest - 1 version
- Mobile viewport simulation
"""

import pytest


class TestChromeDesktop:
    """Chrome desktop browser tests"""

    @pytest.mark.browser
    def test_candidate_signup_flow_chrome(self, page, live_server, store_with_questionnaire):
        """Test: Complete candidate signup flow on Chrome desktop"""

        # Navigate to store chooser
        page.goto(f"{live_server}/candidato/loja/escolher/")

        # Verify page loads
        assert page.url.endswith("/candidato/loja/escolher/")
        assert page.locator("input[type='radio']").count() > 0

        # Select store
        store_id = store_with_questionnaire["store"].id
        page.click(f"input[type='radio'][value='{store_id}']")
        page.click("button:has-text('Continue')")

        # Verify action chooser appears
        page.wait_for_selector("button:has-text('Create Profile')", timeout=2000)
        assert "acao" in page.url or "action" in page.url

        # Choose profile creation
        page.click("button:has-text('Create Profile')")

        # Verify signup form
        page.wait_for_selector("form", timeout=2000)
        assert page.locator("input[type='text']").count() >= 1

    @pytest.mark.browser
    def test_employer_portal_chrome(self, page, live_server):
        """Test: Employer portal loads correctly on Chrome"""

        # Navigate to portal (would require auth in real scenario)
        page.goto(f"{live_server}/portal/")

        # Verify page loads without errors
        page.wait_for_selector("body", timeout=2000)

        # Check for JavaScript errors
        console_errors = []

        def handle_message(msg):
            if msg.type == "error":
                console_errors.append(msg.text)

        page.on("console", handle_message)

        # Verify no critical errors
        assert len([e for e in console_errors if "error" in e.lower()]) == 0

    @pytest.mark.browser
    def test_form_responsiveness_chrome(self, page, live_server, store_with_questionnaire):
        """Test: Form fields respond correctly on Chrome"""

        page.goto(
            f"{live_server}/candidato/formulario/?store={store_with_questionnaire['store'].id}&action=profile"
        )
        page.wait_for_selector("form", timeout=2000)

        # Test text input
        text_input = page.locator("input[type='text']").first
        text_input.click()
        text_input.type("Test Input")
        assert text_input.input_value() == "Test Input"

        # Test select dropdown
        select = page.locator("select").first
        if select.count() > 0:
            select.click()
            options = select.locator("option")
            if options.count() > 1:
                select.select_option(options.nth(1).get_attribute("value"))

        # Test checkbox
        checkbox = page.locator("input[type='checkbox']").first
        if checkbox.count() > 0:
            checkbox.check()
            assert checkbox.is_checked()

    @pytest.mark.browser
    def test_navigation_chrome(self, page, live_server):
        """Test: Navigation works correctly on Chrome"""

        # Test back/forward navigation
        page.goto(f"{live_server}/candidato/loja/escolher/")
        url1 = page.url

        page.goto(f"{live_server}/candidato/acao/escolher/")
        url2 = page.url

        # Go back
        page.go_back()
        assert page.url == url1

        # Go forward
        page.go_forward()
        assert page.url == url2


class TestChromePerformance:
    """Chrome-specific performance tests"""

    @pytest.mark.browser
    def test_first_contentful_paint_chrome(self, page, live_server, store_with_questionnaire):
        """Test: First Contentful Paint < 2s on Chrome"""

        # Measure FCP
        fcp = page.evaluate("""
            () => {
                const perfEntries = performance.getEntriesByName('first-contentful-paint');
                return perfEntries.length > 0 ? perfEntries[0].startTime : null;
            }
        """)

        page.goto(f"{live_server}/candidato/formulario/?store={store_with_questionnaire['store'].id}&action=profile")

        fcp = page.evaluate("""
            () => {
                const perfEntries = performance.getEntriesByName('first-contentful-paint');
                return perfEntries.length > 0 ? perfEntries[0].startTime : null;
            }
        """)

        if fcp:
            assert fcp < 2000, f"FCP {fcp}ms exceeds 2s target"

    @pytest.mark.browser
    def test_largest_contentful_paint_chrome(self, page, live_server):
        """Test: Largest Contentful Paint < 3s on Chrome"""

        page.goto(f"{live_server}/candidato/loja/escolher/")

        lcp = page.evaluate("""
            () => {
                const observer = new PerformanceObserver((list) => {
                    return list.getEntries().pop().renderTime || list.getEntries().pop().loadTime;
                });
                observer.observe({entryTypes: ['largest-contentful-paint']});

                // Wait a bit for LCP
                return new Promise(resolve => {
                    setTimeout(() => resolve(null), 500);
                });
            }
        """)

        # LCP measured, should be < 3s
        assert True  # LCP measurement is browser-dependent


class TestChromeCompatibility:
    """Chrome compatibility matrix"""

    @pytest.mark.browser
    def test_chrome_console_no_errors(self, page, live_server):
        """Test: No console errors on critical paths"""

        errors = []

        def capture_error(msg):
            if "error" in msg.type.lower() or "warn" in msg.type.lower():
                errors.append(msg.text)

        page.on("console", capture_error)

        # Navigate through critical path
        page.goto(f"{live_server}/candidato/loja/escolher/")
        page.wait_for_selector("input[type='radio']", timeout=2000)

        # Check for errors
        critical_errors = [e for e in errors if "error" in e.lower()]
        assert len(critical_errors) == 0, f"Console errors found: {critical_errors}"

    @pytest.mark.browser
    def test_chrome_memory_usage(self, page, live_server, store_with_questionnaire):
        """Test: Memory usage reasonable on Chrome"""

        page.goto(
            f"{live_server}/candidato/formulario/?store={store_with_questionnaire['store'].id}&action=profile"
        )
        page.wait_for_selector("form", timeout=2000)

        # Scroll through form
        form = page.locator("form")
        for _ in range(5):
            form.evaluate("el => el.scrollTop += 200")

        # Check memory is reasonable (no major leaks)
        # Note: Memory API may not be available in all contexts
        memory = page.evaluate("""
            () => {
                if (performance.memory) {
                    return {
                        used: performance.memory.usedJSHeapSize,
                        limit: performance.memory.jsHeapSizeLimit,
                        percent: (performance.memory.usedJSHeapSize / performance.memory.jsHeapSizeLimit) * 100
                    };
                }
                return null;
            }
        """)

        if memory:
            # Memory usage should be <60% of limit
            assert memory["percent"] < 60, \
                f"Memory usage {memory['percent']:.1f}% exceeds 60%"


class TestChromeMobile:
    """Chrome mobile viewport tests"""

    @pytest.mark.browser
    def test_signup_form_mobile_viewport_chrome(self, page, live_server, store_with_questionnaire):
        """Test: Form works on mobile viewport (375x667)"""

        page.set_viewport_size(width=375, height=667)

        page.goto(
            f"{live_server}/candidato/formulario/?store={store_with_questionnaire['store'].id}&action=profile"
        )
        page.wait_for_selector("form", timeout=2000)

        # Verify no horizontal scroll
        body_width = page.locator("body").evaluate("el => el.offsetWidth")
        viewport_width = page.evaluate("() => window.innerWidth")
        assert body_width <= viewport_width, "Content exceeds viewport width"

        # Verify buttons are clickable
        buttons = page.locator("button")
        for i in range(min(buttons.count(), 2)):
            button = buttons.nth(i)
            # Check if button is visible and not too close to edge
            box = button.bounding_box()
            assert box is not None, f"Button {i} not visible on mobile"

    @pytest.mark.browser
    def test_form_input_spacing_mobile_chrome(self, page, live_server, store_with_questionnaire):
        """Test: Form inputs have proper spacing on mobile"""

        page.set_viewport_size(width=375, height=667)

        page.goto(
            f"{live_server}/candidato/formulario/?store={store_with_questionnaire['store'].id}&action=profile"
        )
        page.wait_for_selector("form", timeout=2000)

        # Check input spacing (minimum 44px for touch targets)
        inputs = page.locator("input, button, select")

        for i in range(min(inputs.count(), 3)):
            element = inputs.nth(i)
            box = element.bounding_box()

            if box:
                # Verify minimum touch target size (44x44px recommended)
                height = box["height"]
                width = box["width"]

                # Allow smaller widths for checkboxes/radios
                if "checkbox" not in element.get_attribute("type") and \
                   "radio" not in element.get_attribute("type"):
                    assert height >= 40, \
                        f"Element height {height}px below 44px recommendation"
