""" Logic views """

import json

from django.shortcuts import render

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from logic import services

@csrf_exempt
def analyze(request):
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

        return JsonResponse({"status": "ok", "user_id": user_id, "result": res})

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)