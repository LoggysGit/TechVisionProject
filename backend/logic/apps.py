""" Logic apps """

import os
import sys
from django.apps import AppConfig

class LogicConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'logic'

    def ready(self):
        if 'runserver' not in sys.argv:
            return

        is_run_main = os.environ.get('RUN_MAIN') == 'true'
        is_noreload = '--noreload' in sys.argv

        if is_run_main or is_noreload:
            from logic.services import LawRetriever, AIService
            
            print("\n[Setup] System setup...")
            AIService.download_local_model()
            LawRetriever.build_law_index()
            print("[Setup] Project setup. Starting...\n")