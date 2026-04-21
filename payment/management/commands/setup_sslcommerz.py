from django.core.management.base import BaseCommand
from payment.models import PaymentGatewayConfig


class Command(BaseCommand):
    help = 'Configure SSLCommerz payment gateway credentials'

    def add_arguments(self, parser):
        parser.add_argument('--store-id', type=str, help='SSLCommerz Store ID')
        parser.add_argument('--store-password', type=str, help='SSLCommerz Store Password')
        parser.add_argument('--sandbox', action='store_true', default=True, help='Use sandbox mode')
        parser.add_argument('--live', action='store_true', help='Use live mode')

    def handle(self, *args, **options):
        store_id = options.get('store_id')
        store_password = options.get('store_password')
        
        if not store_id or not store_password:
            self.stdout.write(self.style.ERROR('Store ID and Store Password are required'))
            return
        
        is_sandbox = options.get('sandbox') and not options.get('live')
        
        # Delete existing config if any
        PaymentGatewayConfig.objects.all().delete()
        
        # Create new config
        config = PaymentGatewayConfig.objects.create(
            store_id=store_id,
            store_password=store_password,
            is_sandbox=is_sandbox,
            is_active=True
        )
        
        mode = 'Sandbox' if is_sandbox else 'Live'
        self.stdout.write(
            self.style.SUCCESS(
                f'SSLCommerz configuration updated successfully!\n'
                f'Store ID: {store_id}\n'
                f'Mode: {mode}\n'
                f'Session API: {config.session_api_url}\n'
                f'Validation API: {config.validation_api_url}'
            )
        )
