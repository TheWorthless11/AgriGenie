"""
Django management commands for AgriGenie
"""
from django.core.management.base import BaseCommand
from admin_panel.models import AIDiseaseMonitor, AIPricePredictor, ActivityLog


class Command(BaseCommand):
    help = 'Initialize AI monitoring models and activity logging'

    def handle(self, *args, **options):
        # Create initial AI monitoring records if they don't exist
        disease_monitor, created = AIDiseaseMonitor.objects.get_or_create(
            id=1,
            defaults={
                'total_detections': 0,
                'accurate_detections': 0,
                'accuracy_percentage': 0,
                'model_version': '1.0'
            }
        )
        
        price_predictor, created = AIPricePredictor.objects.get_or_create(
            id=1,
            defaults={
                'total_predictions': 0,
                'accurate_predictions': 0,
                'accuracy_percentage': 0,
                'average_error_percentage': 0,
                'model_version': '1.0'
            }
        )
        
        self.stdout.write(self.style.SUCCESS('✓ AI Monitoring initialized successfully'))
        self.stdout.write(f'  Disease Monitor: {disease_monitor.id}')
        self.stdout.write(f'  Price Predictor: {price_predictor.id}')
