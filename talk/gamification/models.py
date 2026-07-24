from datetime import datetime

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings



class GamificationSettings(models.Model):
    description = models.CharField(
        max_length=50, unique=True, verbose_name=_("Description"))

    # ap_ prefix for 'award points'
    # dp_ prefix for 'default points'

    ap_first_login = models.BooleanField(
        default=False, verbose_name=_('First Login'))
    dp_first_login = models.IntegerField(
        default=1, verbose_name=_('First Login Points'))

    ap_feed_post_view = models.BooleanField(
        default=False, verbose_name=_('Feed Post View'))
    dp_feed_post_view = models.IntegerField(
        default=1, verbose_name=_('Feed Post View Points'))

    ap_course_enrollment = models.BooleanField(
        default=False, verbose_name=_('Course Enrollment'))
    dp_course_enrollment = models.IntegerField(
        default=1, verbose_name=_('Course Enrollment Points'))

    ap_course_completation = models.BooleanField(
        default=False, verbose_name=_('Course Completation'))
    dp_course_completation = models.IntegerField(
        default=1, verbose_name=_('Course Completation Points'))

    ap_passed_tests = models.BooleanField(
        default=False, verbose_name=_('Passed Tests'))
    dp_passed_tests = models.IntegerField(
        default=1, verbose_name=_('Passed Tests Points'))

    class Meta:
        verbose_name = _("Gamification Settings")
        verbose_name_plural = _("Gamification Settings")

    def __str__(self):
        return self.description


class GamificationReport(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='gamification_report', on_delete=models.CASCADE)
    date_time_event = models.DateTimeField(auto_now_add=True)
    points = models.IntegerField()
    type_event = models.CharField(verbose_name=_("Type event"), max_length=30, choices=[
                                  ('login', _('Login')),
                                  ('post_view', _('Post View')),
                                  ('course_enrollment', _('Course Enrollment')),
                                  ('course_completation', _('Course Completation')),
                                  ('passed_tests', _('Passed Tests'))])
    model_name = models.CharField(verbose_name=_("Model of record"), max_length=30, null=True)
    id_source = models.PositiveIntegerField(verbose_name=_("Id source object"), null=True)

    class Meta:
        verbose_name = _("Gamification Report")
        verbose_name_plural = _("Gamification Report")

    def __str__(self):
        return f"{self.points} - {self.type_event}"


class GamificationPostView(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='post_views', on_delete=models.CASCADE)
    feed_post = models.ForeignKey(
        'publishing.Publication', related_name='post_views', on_delete=models.CASCADE)

    class Meta:
        verbose_name = _("Gamification Post View")
        verbose_name_plural = _("Gamification Post Views")


class Badges(models.Model):
    qty_points = models.PositiveIntegerField(unique=True, verbose_name=_("Quantity points"))
    image = models.ImageField(upload_to='gamification/badges/', verbose_name=_("Image"), null=True, blank=True)
    name = models.CharField(max_length=30, verbose_name=_("Name"))
