from django.test import SimpleTestCase

from .services import calculate_progress


class ProgressCalculationTests(SimpleTestCase):
    def test_empty_course_has_zero_progress(self):
        self.assertEqual(calculate_progress(0, 0), 0)

    def test_progress_is_percentage(self):
        self.assertEqual(calculate_progress(4, 1), 25)

    def test_progress_never_exceeds_one_hundred(self):
        self.assertEqual(calculate_progress(2, 3), 100)
