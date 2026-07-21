""" URL configuration for core project. """

from django.contrib import admin
from django.urls import path, include

#from dj_rest_auth.registration.views import SocialLoginView

#from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
#from allauth.socialaccount.providers.oauth2.client import OAuth2Client

from django.http import JsonResponse
from users import views as users_views
from logic import views as logic_views

urlpatterns = [
    path('', lambda request: JsonResponse({"status": "ok", "message": "Website API service is running properly."}), name='api-root'),

    path('admin/', admin.site.urls),
    
    path('api/auth/', include('dj_rest_auth.urls')), 

    # Analyze request
    path('api/analyze/', logic_views.analyze),
]
