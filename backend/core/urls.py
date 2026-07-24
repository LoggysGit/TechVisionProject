""" URL configuration for core project. """

from django.contrib import admin
from django.urls import path, include

from django.http import JsonResponse
from logic import views as logic_views

urlpatterns = [
    path('', lambda request: JsonResponse({"status": "ok", "message": "Website API service is running properly."}), name='api-root'),

    path('admin/', admin.site.urls),

    # Analyze request
    path('api/analyze/', logic_views.analyze),
]
