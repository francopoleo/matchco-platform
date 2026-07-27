from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from tenants_core.models import TenantUser


class ContentItem(models.Model):
    TEXT = 'text'
    VIDEO = 'video'
    IMAGE = 'image'
    FILE = 'file'
    KIND_CHOICES = (
        (TEXT, 'Text'),
        (VIDEO, 'Video'),
        (IMAGE, 'Image'),
        (FILE, 'File'),
    )

    module = models.ForeignKey(
        'courses.Module',
        related_name='library_items',
        on_delete=models.CASCADE,
    )
    kind = models.CharField(max_length=16, choices=KIND_CHOICES)
    title = models.CharField(max_length=250)
    description = models.TextField(blank=True)
    body = models.TextField(blank=True)
    video_url = models.URLField(blank=True)
    file = models.FileField(upload_to='learning/files/', blank=True)
    image = models.ImageField(upload_to='learning/images/', blank=True)
    owner = models.ForeignKey(
        TenantUser,
        related_name='library_items_created',
        on_delete=models.PROTECT,
    )
    published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('module', 'id')

    def __str__(self):
        return self.title

    @property
    def is_published(self):
        return self.published

    def clean(self):
        errors = {}
        if self.kind == self.VIDEO and not self.video_url:
            errors['video_url'] = 'A video URL is required for video content.'
        if self.kind == self.FILE and not self.file:
            errors['file'] = 'A file is required for file content.'
        if self.kind == self.IMAGE and not self.image:
            errors['image'] = 'An image is required for image content.'
        if self.kind == self.TEXT and not self.body:
            errors['body'] = 'Text content cannot be empty.'
        if errors:
            raise ValidationError(errors)


class ContentItemProgress(models.Model):
    item = models.ForeignKey(ContentItem, related_name='progress', on_delete=models.CASCADE)
    user = models.ForeignKey(TenantUser, related_name='library_progress', on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ('-completed_at', '-id')
        unique_together = (('item', 'user'),)
