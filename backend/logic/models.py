""" Logic model """

from django.db import models
from django.contrib.auth.models import User

from django.utils import timezone

def user_directory_path(instance, filename):
    """ Returns user file path """
    now = timezone.now().strftime('%Y%m%d_%H%M%S')
    return f'{instance.user.id}/reports/{now}_{filename}'

class Report:
    """ Report data """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='oauth_accounts')

    uploaded_file = models.FileField(upload_file_to=user_directory_path, null=True, blank=True)
    
    ai_analysis_result = models.JSONField(default=dict, blank=True)
    
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report {self.id} for {self.user.email}"