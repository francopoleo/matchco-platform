from django.db import transaction

from courses.models import Content
from students.models import CourseEnroll, ContentEnroll, ModuleEnroll


def get_enrollment(user, course):
    return CourseEnroll.objects.filter(student_id=user, course_id=course).first()


@transaction.atomic
def enroll_user(user, course):
    enrollment, created = CourseEnroll.objects.get_or_create(
        student_id=user,
        course_id=course,
    )
    course.students.add(user)
    return enrollment, created


def calculate_progress(total_items, completed_items):
    if total_items <= 0:
        return 0
    completed_items = min(completed_items, total_items)
    return (completed_items / total_items) * 100


def enrollment_progress(enrollment):
    total_items = Content.objects.filter(module__course=enrollment.course_id).count()
    completed_items = ContentEnroll.objects.filter(
        module_enroll_id__course_enroll_id=enrollment,
        done=True,
    ).count()
    return calculate_progress(total_items, completed_items)


@transaction.atomic
def mark_content_completed(user, content):
    enrollment = get_enrollment(user, content.module.course)
    if enrollment is None:
        return None

    module_enrollment, _ = ModuleEnroll.objects.get_or_create(
        course_enroll_id=enrollment,
        module_id=content.module,
    )
    content_enrollment, _ = ContentEnroll.objects.get_or_create(
        module_enroll_id=module_enrollment,
        content_id=content,
    )
    content_enrollment.done = True
    if content.content_type.model == 'quiz':
        content_enrollment.quiz_id = content.item
    content_enrollment.save(update_fields=['done', 'quiz_id'])
    return content_enrollment
