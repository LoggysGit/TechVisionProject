""" Logic views """

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from logic import services

@csrf_exempt
def analyze(request):
    # 1. CORS preflight
    if request.method == 'OPTIONS':
        response = JsonResponse({}, status=200)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    # 2. Method check
    if request.method != 'POST':
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)
        user_id = data.get("user_id")
        content = data.get("content")

        # Get info about user from DB (NOT NOW)
        user = {"tier": "free", "name": "Guest"}

        docproc = services.DocumentProcessor()
        res = docproc.analyze(content, user)

        # Update Report DB (NOT NOW)

        # 3. Form & Send
        response = JsonResponse({"user_id": user_id, "result": res}, status=200)
        response["Access-Control-Allow-Origin"] = "*"
        return response

    except json.JSONDecodeError:
        response = JsonResponse({"error": "Invalid JSON"}, status=400)
        response["Access-Control-Allow-Origin"] = "*"
        return response

    except Exception as e:
        response = JsonResponse({"error": str(e)}, status=500)
        response["Access-Control-Allow-Origin"] = "*"
        return response