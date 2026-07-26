from django import template
import re
from urllib.parse import parse_qs, urlparse
from ..models import ModuleEnroll, ContentEnroll, CourseEnroll
from learning.services import enrollment_progress, get_enrollment

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


@register.simple_tag(name="check_content_is_done")
def check_content_is_done(content, course_enroll):
    module_enroll = ModuleEnroll.objects.filter(course_enroll_id=course_enroll, module_id=content.module)
    if module_enroll:
        module_enroll = module_enroll.first()
        content_enroll = ContentEnroll.objects.filter(module_enroll_id=module_enroll, content_id=content)
        if content_enroll:
            content_enroll = content_enroll.first()
            return content_enroll.done
    return False


@register.simple_tag(name="check_module_is_done")
def check_module_is_done(module, course_enroll):
    module_enroll = ModuleEnroll.objects.filter(course_enroll_id=course_enroll, module_id=module)
    if module_enroll:
        module_enroll = module_enroll.first()
        all_content = module.get_content()
        if not all_content:
            return False
        for content in all_content:
            content_enroll = ContentEnroll.objects.filter(module_enroll_id=module_enroll, content_id=content)
            if not content_enroll or not content_enroll.first().done:
                return False
        return True
    return False


@register.simple_tag(name="get_course_progress")
def get_course_progress(course, user):
    course_enroll = get_enrollment(user, course)
    if not course_enroll:
        return 0

    return enrollment_progress(course_enroll)


@register.simple_tag(name="get_your_question_result")
def get_your_question_result(quiz_result, current_question):
    return quiz_result.questions.all().filter(question_id=current_question.get('id')).first()
