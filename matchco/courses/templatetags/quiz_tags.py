from django import template

register = template.Library()


@register.simple_tag(name="get_quiz_data")
def get_quiz_data(quiz):
    questions = []
    for index, q in enumerate(quiz.get_questions()):
        answers = []
        for a in q.get_answers():
            answers.append({
                'id': a.id,
                'text': a.text,
            })
        questions.append(
            {
                'id': q.id,
                'text': q.text,
                'answers': answers,
                'index': index
            }
        )
    return {
        'questions': questions,
        'total_questions': len(questions)
    }
