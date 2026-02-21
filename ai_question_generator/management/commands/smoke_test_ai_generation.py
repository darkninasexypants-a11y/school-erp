from django.core.management.base import BaseCommand
from ai_question_generator.generator import generate_questions
from students_app.models import MockTest, MockTestQuestion


class Command(BaseCommand):
    help = 'Smoke test: generate a few AI-style questions for the latest MockTest'

    def handle(self, *args, **kwargs):
        # Pick the latest MockTest if available, otherwise create a lightweight one
        mock = MockTest.objects.order_by('-id').first()
        if not mock:
            mock = MockTest.objects.create(
                title='Demo AI MockTest',
                total_marks=50,
                time_limit=60,
                description='Generated for AI smoke test'
            )

        subject = 'Physics'
        topics = 'Kinematics, Dynamics'
        questions = generate_questions(subject, topics, count=3, difficulty='easy')

        created = []
        for q in questions:
            obj, created_flag = MockTestQuestion.objects.get_or_create(mock_test=mock, question_text=q)
            if created_flag:
                created.append(obj.question_text)

        self.stdout.write(self.style.SUCCESS(f"Generated {len(created)} questions for MockTest {mock.id}:"))
        for q_text in created:
            self.stdout.write(f" - {q_text}")





