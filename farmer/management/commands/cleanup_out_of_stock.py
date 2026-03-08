"""
Management command to clean up crops that have been out of stock for 24+ hours.
Can be run via cron job or manually: python manage.py cleanup_out_of_stock
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from farmer.models import Crop
from users.models import Notification
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Delete crop listings that have been out of stock for more than 24 hours'

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(hours=24)
        
        expired_crops = Crop.objects.filter(
            is_available=False,
            out_of_stock_since__isnull=False,
            out_of_stock_since__lte=cutoff
        )
        
        count = 0
        for crop in expired_crops:
            farmer = crop.farmer
            crop_name = crop.crop_name
            
            Notification.objects.create(
                user=farmer,
                notification_type='system',
                title=f'Crop Removed: {crop_name}',
                message=f'Your listing for {crop_name} was automatically removed because it was out of stock for over 24 hours.'
            )
            
            self.stdout.write(f"Deleting: {crop_name} (ID: {crop.id}) by {farmer.username}")
            crop.delete()
            count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Cleaned up {count} out-of-stock crop(s)'))
