from django.conf import settings
from django.db import models
from django.utils import timezone

from audience.models import AudiencePolicy


class Tag(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=90, unique=True)

    def __str__(self):
        return self.name


class Publication(models.Model):
    WIKI = 'wiki'
    FEED = 'feed'
    KINDS = ((WIKI, 'Wiki'), (FEED, 'Feed'))
    DRAFT = 'draft'
    PUBLISHED = 'published'
    STATUS_CHOICES = ((DRAFT, 'Draft'), (PUBLISHED, 'Published'))

    kind = models.CharField(max_length=8, choices=KINDS)
    organization = models.ForeignKey('configuration.Organization', null=True, blank=True, related_name='publications', on_delete=models.CASCADE)
    title = models.CharField(max_length=220)
    slug = models.SlugField(max_length=240, unique=True)
    excerpt = models.TextField(blank=True)
    body = models.TextField()
    image = models.ImageField(upload_to='publishing/images/', blank=True)
    video_url = models.URLField(blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='publications', on_delete=models.PROTECT)
    audience_policy = models.ForeignKey(AudiencePolicy, null=True, blank=True, on_delete=models.SET_NULL)
    tags = models.ManyToManyField(Tag, blank=True, related_name='publications')
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=DRAFT)
    published_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    points_per_view = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-published_at', '-created_at')

    def __str__(self):
        return self.title

    @property
    def is_published(self):
        return self.status == self.PUBLISHED and self.published_at is not None and not self.is_expired

    @property
    def is_expired(self):
        return bool(self.expires_at and self.expires_at <= timezone.now())
