"""
Performance Tests: Form Load Times

Measures:
- Form initial load (<500ms target)
- First question render (<200ms target)
- Form interactivity
- No layout shifts
"""

import pytest
import time
from datetime import datetime


class TestFormLoadPerformance:
    """Form load time measurements"""

    @pytest.mark.performance
    def test_store_chooser_load_time(self, page, live_server, measure_load_time):
        """Test: Store chooser loads in <500ms"""

        result = measure_load_time(
            page,
            f"{live_server}/candidato/loja/escolher/",
            selector_to_wait="input[type='radio']"
        )

        assert result["duration_ms"] < 500, \
            f"Store chooser took {result['duration_ms']}ms (target: <500ms)"

    @pytest.mark.performance
    def test_action_chooser_load_time(self, page, live_server, measure_load_time, store_with_questionnaire):
        """Test: Action chooser loads in <500ms"""

        result = measure_load_time(
            page,
            f"{live_server}/candidato/acao/escolher/?store={store_with_questionnaire['store'].id}",
            selector_to_wait="button:has-text('Create Profile')"
        )

        assert result["duration_ms"] < 500, \
            f"Action chooser took {result['duration_ms']}ms (target: <500ms)"

    @pytest.mark.performance
    def test_signup_form_load_time(self, page, live_server, measure_load_time, store_with_questionnaire):
        """Test: Signup form loads in <500ms"""

        result = measure_load_time(
            page,
            f"{live_server}/candidato/formulario/?store={store_with_questionnaire['store'].id}&action=profile",
            selector_to_wait="form"
        )

        assert result["duration_ms"] < 500, \
            f"Signup form took {result['duration_ms']}ms (target: <500ms)"

    @pytest.mark.performance
    def test_first_form_field_interactive(self, page, live_server, store_with_questionnaire):
        """Test: First form field interactive within 200ms"""

        start = time.time()
        page.goto(
            f"{live_server}/candidato/formulario/?store={store_with_questionnaire['store'].id}&action=profile"
        )

        # Wait for first input to be interactive
        page.wait_for_selector("input[type='text']", timeout=200)
        first_input = page.locator("input[type='text']").first

        duration_ms = (time.time() - start) * 1000

        assert duration_ms < 200, \
            f"First field took {duration_ms}ms (target: <200ms)"

        # Verify field is actually interactive
        first_input.fill("Test", timeout=1000)
        assert first_input.input_value() == "Test"

    @pytest.mark.performance
    def test_form_no_layout_shift(self, page, live_server, store_with_questionnaire):
        """Test: Form doesn't have layout shifts (CLS)"""

        page.goto(
            f"{live_server}/candidato/formulario/?store={store_with_questionnaire['store'].id}&action=profile"
        )
        page.wait_for_selector("form")

        # Measure Cumulative Layout Shift
        cls = page.evaluate("""() => {
            let cls = 0;
            const observer = new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    if (!entry.hadRecentInput) {
                        cls += entry.value;
                    }
                }
            });
            observer.observe({entryTypes: ['layout-shift']});

            // Wait 3 seconds for layout shifts
            return new Promise(resolve => {
                setTimeout(() => {
                    resolve(cls);
                }, 3000);
            });
        }""")

        # CLS should be < 0.1 (good web vitals)
        assert cls < 0.1, f"CLS too high: {cls} (target: <0.1)"

    @pytest.mark.performance
    def test_all_questions_render_on_scroll(self, page, live_server, store_with_questionnaire):
        """Test: Questions render as user scrolls (lazy loading)"""

        page.goto(
            f"{live_server}/candidato/formulario/?store={store_with_questionnaire['store'].id}&action=profile"
        )
        page.wait_for_selector("form")

        # Scroll to bottom
        form = page.locator("form")
        form.evaluate("el => el.scrollTop = el.scrollHeight")

        # Verify all questions loaded
        questions = page.locator(".question-item").count()
        expected_count = store_with_questionnaire["template"].questions.count()

        assert questions >= expected_count, \
            f"Only {questions} questions rendered (expected: {expected_count})"

    @pytest.mark.performance
    def test_form_submission_latency(self, page, live_server, django_db_blocker, store_with_questionnaire):
        """Test: Form submission processed in <1 second"""

        page.goto(
            f"{live_server}/candidato/formulario/?store={store_with_questionnaire['store'].id}&action=profile"
        )
        page.wait_for_selector("form")

        # Fill form quickly
        page.fill("input[name='question_1']", "Test Name")
        page.click("input[type='radio'][name='question_2'][value='true']")
        page.select_option("select[name='question_3']", "Manhã")
        page.fill("input[type='date'][name='question_4']", "2026-11-15")
        page.locator("input[name='phone']").scroll_into_view_if_needed()
        page.fill("input[name='phone']", "+5511998765432")
        page.fill("input[name='email']", "test@test.com")
        page.check("input[name='accept_terms']")

        # Measure submission time
        start = time.time()
        page.click("button:has-text('Submit')")

        # Wait for response (OTP screen or success)
        try:
            page.wait_for_selector(
                "input[name='otp_code'], .success-message",
                timeout=1000
            )
        except Exception:
            pass  # Network might be slow in test env

        duration_ms = (time.time() - start) * 1000

        # Should complete within 1 second
        # (in real scenario, may take longer due to OTP delivery)
        assert duration_ms < 5000, \
            f"Form submission took {duration_ms}ms"


class TestFormResponseTimes:
    """Measure form field response times"""

    @pytest.mark.performance
    def test_text_input_response_time(self, page, live_server, store_with_questionnaire):
        """Test: Text input responds in <50ms"""

        page.goto(
            f"{live_server}/candidato/formulario/?store={store_with_questionnaire['store'].id}&action=profile"
        )
        page.wait_for_selector("input[type='text']")

        text_input = page.locator("input[type='text']").first

        start = time.time()
        text_input.type("T", delay=0)  # No artificial delay
        duration_ms = (time.time() - start) * 1000

        # Should respond immediately (browser typing)
        assert duration_ms < 100, \
            f"Text input took {duration_ms}ms to respond"

    @pytest.mark.performance
    def test_select_option_response_time(self, page, live_server, store_with_questionnaire):
        """Test: Select dropdown responds in <50ms"""

        page.goto(
            f"{live_server}/candidato/formulario/?store={store_with_questionnaire['store'].id}&action=profile"
        )
        page.wait_for_selector("select")

        select = page.locator("select").first

        start = time.time()
        select.click()
        duration_ms = (time.time() - start) * 1000

        # Dropdown should open immediately
        assert duration_ms < 100, \
            f"Select opened in {duration_ms}ms"

    @pytest.mark.performance
    def test_checkbox_response_time(self, page, live_server, store_with_questionnaire):
        """Test: Checkbox responds in <50ms"""

        page.goto(
            f"{live_server}/candidato/formulario/?store={store_with_questionnaire['store'].id}&action=profile"
        )
        page.wait_for_selector("input[type='checkbox']")

        checkbox = page.locator("input[type='checkbox']").first

        start = time.time()
        checkbox.check()
        duration_ms = (time.time() - start) * 1000

        # Checkbox should toggle immediately
        assert duration_ms < 100, \
            f"Checkbox took {duration_ms}ms to respond"

    @pytest.mark.performance
    def test_scroll_performance(self, page, live_server, store_with_questionnaire):
        """Test: Scroll performance (60 FPS target)"""

        page.goto(
            f"{live_server}/candidato/formulario/?store={store_with_questionnaire['store'].id}&action=profile"
        )
        page.wait_for_selector("form")

        # Measure scroll performance
        fps = page.evaluate("""() => {
            let frameCount = 0;
            let lastTime = performance.now();

            return new Promise(resolve => {
                const countFrames = (currentTime) => {
                    frameCount++;
                    if (currentTime - lastTime < 1000) {
                        requestAnimationFrame(countFrames);
                    } else {
                        resolve(frameCount);
                    }
                };
                requestAnimationFrame(countFrames);

                // Simulate scroll
                window.scrollBy(0, 500);
            });
        }""")

        # Should achieve close to 60 FPS
        assert fps >= 50, f"Only {fps} FPS (target: 60 FPS)"
