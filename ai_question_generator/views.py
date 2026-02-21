import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from .generator import generate_questions
from students_app.models import MockTest

@csrf_exempt
def ai_generate_questions(request, mock_test_id):
    """
    API endpoint to generate questions for a given MockTest.
    Expects POST with JSON body:
    {
      "subject": "Physics",
      "topics": "Kinematics, Dynamics",
      "count": 5,
      "difficulty": "medium"
    }
    """
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("Invalid JSON")

    subject = payload.get("subject", "")
    topics = payload.get("topics", "")
    count = int(payload.get("count", 5))
    difficulty = payload.get("difficulty", "medium")

    questions = generate_questions(subject, topics, count, difficulty)

    mock = MockTest.objects.filter(id=mock_test_id).first()
    created = []
    if mock:
        from students_app.models import MockTestQuestion
        for q in questions:
            obj, _ = MockTestQuestion.objects.get_or_create(mock_test=mock, question_text=q)
            created.append(obj.question_text)

    return JsonResponse({"generated": created, "mock_test_id": mock_test_id})


