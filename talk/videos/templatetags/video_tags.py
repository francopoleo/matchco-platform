from django import template
from videos.models import VideoContent

register = template.Library()


@register.simple_tag(name="get_video_count")
def get_video_count():
        count = VideoContent.objects.all().count()
        return count