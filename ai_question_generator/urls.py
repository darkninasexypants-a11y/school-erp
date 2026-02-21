from django.urls import path
from .views import ai_generate_questions

urlpatterns = [
    path('generate/<int:mock_test_id>/', ai_generate_questions, name='ai_generate_questions'),
]

