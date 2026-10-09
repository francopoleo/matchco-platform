from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from courses.models import Course, Module, Quiz, Question, Answer
from organizations.models import Organization

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample hospital course data with quizzes and questions'

    def add_arguments(self, parser):
        parser.add_argument('org_id', type=int, help='Organization ID')
        parser.add_argument('--user-id', type=int, help='Owner user ID (defaults to first admin)')

    def handle(self, *args, **options):
        org_id = options['org_id']
        org = Organization.objects.get(id=org_id)

        if options['user_id']:
            owner = User.objects.get(id=options['user_id'])
        else:
            owner = User.objects.filter(is_staff=True).first()
            if not owner:
                self.stdout.write(self.style.ERROR('No admin user found. Provide --user-id'))
                return

        # Create main course
        course = Course.objects.create(
            title='Segurança do Paciente e Protocolos Hospitalares',
            overview='Capacitação sobre protocolos essenciais de segurança e qualidade da assistência hospitalar',
            organization=org,
            owner=owner,
            state='published'
        )
        self.stdout.write(self.style.SUCCESS(f'✓ Curso criado: {course.title}'))

        # Module 1: Hand Hygiene
        module1 = Module.objects.create(
            course=course,
            title='Higiene das Mãos e Prevenção de Infecções',
            description='Procedimentos fundamentais para higiene de mãos e prevenção de infecções cruzadas',
            order=1
        )

        quiz1 = Quiz.objects.create(
            title='Quiz: Higiene das Mãos',
            overview='Teste seu conhecimento sobre higiene de mãos e seus protocolos',
            quiz_type='formative',
            required_score_to_pass=70,
            is_required=True,
            owner=owner,
            organization=org
        )

        # Question 1.1
        q1 = Question.objects.create(
            quiz=quiz1,
            question_type='multiple_choice',
            text='Em qual momento é obrigatório lavar as mãos ANTES do contato com o paciente?',
            explanation='A higiene das mãos antes do contato direto é essencial para prevenir a transmissão de patógenos ao paciente.',
            order=1
        )
        Answer.objects.create(question=q1, text='Ao chegar na enfermaria, mesmo com luvas', correct=True)
        Answer.objects.create(question=q1, text='Apenas quando visível sujo', correct=False)
        Answer.objects.create(question=q1, text='Somente entre pacientes diferentes', correct=False)
        Answer.objects.create(question=q1, text='Nunca, as luvas são suficientes', correct=False)

        # Question 1.2
        q2 = Question.objects.create(
            quiz=quiz1,
            question_type='true_false',
            text='Verdadeiro ou Falso: Usar luvas dispensa a necessidade de lavar as mãos.',
            explanation='FALSO. As luvas devem ser usadas em conjunto com a higiene das mãos. Mãos contaminadas podem contaminar as luvas.',
            order=2
        )
        Answer.objects.create(question=q2, text='Verdadeiro', correct=False)
        Answer.objects.create(question=q2, text='Falso', correct=True)

        # Question 1.3
        q3 = Question.objects.create(
            quiz=quiz1,
            question_type='multiple_choice',
            text='Qual é a duração recomendada para lavar as mãos adequadamente?',
            explanation='Minutos 40-60 segundos é o tempo ideal para remover a maioria dos patógenos das mãos.',
            order=3
        )
        Answer.objects.create(question=q3, text='10-15 segundos', correct=False)
        Answer.objects.create(question=q3, text='40-60 segundos', correct=True)
        Answer.objects.create(question=q3, text='2-3 minutos', correct=False)
        Answer.objects.create(question=q3, text='Quanto mais longo, melhor', correct=False)

        self.stdout.write(self.style.SUCCESS(f'✓ Módulo 1 criado com {q3.order} perguntas'))

        # Module 2: Patient Identification
        module2 = Module.objects.create(
            course=course,
            title='Identificação Segura do Paciente',
            description='Protocolos para garantir a identificação correta e prevenir erros de medicação',
            order=2
        )

        quiz2 = Quiz.objects.create(
            title='Quiz: Identificação de Pacientes',
            overview='Validar conhecimento sobre procedimentos de identificação de pacientes',
            quiz_type='formative',
            required_score_to_pass=75,
            is_required=True,
            owner=owner,
            organization=org
        )

        # Question 2.1
        q4 = Question.objects.create(
            quiz=quiz2,
            question_type='multiple_choice',
            text='Qual é o padrão internacional para identificação de pacientes?',
            explanation='Usar pelo menos 2 identificadores é o padrão ouro recomendado pela Joint Commission.',
            order=1
        )
        Answer.objects.create(question=q4, text='1 identificador (nome)', correct=False)
        Answer.objects.create(question=q4, text='2 identificadores (nome + data de nascimento)', correct=True)
        Answer.objects.create(question=q4, text='3 identificadores', correct=False)
        Answer.objects.create(question=q4, text='Apenas número de leito', correct=False)

        # Question 2.2
        q5 = Question.objects.create(
            quiz=quiz2,
            question_type='multiple_choice',
            text='Antes de administrar medicação, qual procedimento é essencial?',
            explanation='Confirmar a identidade do paciente usando 2 identificadores reduz em 95% os erros de medicação.',
            order=2
        )
        Answer.objects.create(question=q5, text='Olhar o prontuário', correct=False)
        Answer.objects.create(question=q5, text='Perguntar o nome e data de nascimento', correct=True)
        Answer.objects.create(question=q5, text='Apenas verificar a pulseira de identificação', correct=False)
        Answer.objects.create(question=q5, text='Confiar na informação do acompanhante', correct=False)

        self.stdout.write(self.style.SUCCESS(f'✓ Módulo 2 criado com {q5.order} perguntas'))

        # Module 3: Infection Control
        module3 = Module.objects.create(
            course=course,
            title='Controle de Infecções Relacionadas à Assistência',
            description='Medidas de biossegurança e prevenção de infecções hospitalares',
            order=3
        )

        quiz3 = Quiz.objects.create(
            title='Quiz: Controle de Infecções',
            overview='Avaliar conhecimento sobre prevenção de infecções',
            quiz_type='exam',
            required_score_to_pass=80,
            is_required=True,
            owner=owner,
            organization=org
        )

        # Question 3.1
        q6 = Question.objects.create(
            quiz=quiz3,
            question_type='multiple_choice',
            text='Qual equipamento de proteção individual (EPI) é obrigatório para precaução padrão?',
            explanation='Luvas, máscara, protetor ocular e avental são recomendados quando há risco de exposição a sangue ou fluidos.',
            order=1
        )
        Answer.objects.create(question=q6, text='Apenas luvas', correct=False)
        Answer.objects.create(question=q6, text='Luvas, máscara, protetor ocular e avental', correct=True)
        Answer.objects.create(question=q6, text='Nenhum EPI é necessário', correct=False)
        Answer.objects.create(question=q6, text='Apenas máscara N95', correct=False)

        # Question 3.2
        q7 = Question.objects.create(
            quiz=quiz3,
            question_type='true_false',
            text='Verdadeiro ou Falso: Objetos reutilizáveis podem ser compartilhados entre pacientes sem desinfecção.',
            explanation='FALSO. Todos os objetos reutilizáveis devem ser desinfetados após cada uso para prevenir infecções cruzadas.',
            order=2
        )
        Answer.objects.create(question=q7, text='Verdadeiro', correct=False)
        Answer.objects.create(question=q7, text='Falso', correct=True)

        self.stdout.write(self.style.SUCCESS(f'✓ Módulo 3 criado com {q7.order} perguntas'))

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Dados de exemplo criados com sucesso!\n'
            f'   Curso: {course.title}\n'
            f'   Módulos: {course.modules.count()}\n'
            f'   Quizzes: {Quiz.objects.filter(owner=owner, organization=org).count()}\n'
            f'   Perguntas: {Question.objects.filter(quiz__owner=owner, quiz__organization=org).count()}'
        ))
