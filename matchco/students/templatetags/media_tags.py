import re
from urllib.parse import parse_qs, urlparse

from django import template

register = template.Library()


@register.filter
def youtube_embed_url(value):
    """Return a privacy-enhanced YouTube embed URL for common YouTube links."""
    if not value:
        return ''

    raw = str(value).strip()
    parsed = urlparse(raw if '://' in raw else f'https://{raw}')
    host = parsed.netloc.lower().split(':')[0]
    video_id = ''

    if host in {'youtu.be', 'www.youtu.be'}:
        video_id = parsed.path.strip('/').split('/')[0]
    elif host.endswith('youtube.com'):
        query_id = parse_qs(parsed.query).get('v', [''])[0]
        if '/embed/' in parsed.path or '/shorts/' in parsed.path:
            video_id = parsed.path.split('/')[-1]
        else:
            video_id = query_id

    if not re.fullmatch(r'[A-Za-z0-9_-]{11}', video_id or ''):
        return ''

    return f'https://www.youtube-nocookie.com/embed/{video_id}?rel=0&modestbranding=1&playsinline=1'
