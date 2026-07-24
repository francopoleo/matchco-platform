from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from taggit.managers import TaggableManager


# Create your models here.
class VideoContent(models.Model):
    title = models.CharField(max_length=50, null=True)
    url = models.URLField(null=True)
    banner = models.ImageField(upload_to='videos/banners/', null=True, blank=True)
    tags = TaggableManager(help_text=None, blank=True, verbose_name='Tags')

    create_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_('Created by user'),
        null=True, blank=True, editable=False, on_delete=models.SET_NULL
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Video'
        verbose_name_plural = 'Videos'
        permissions = [
            ("choose_video", "Can choose videos"),
        ]
