from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from users.models import CustomUser


class Command(BaseCommand):
    help = 'Delete user accounts that have not been verified within 30 days of registration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show which accounts would be deleted without actually deleting them',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to wait before deleting unverified accounts (default: 30)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        days = options['days']
        
        deadline = timezone.now() - timedelta(days=days)
        
        unverified_accounts = CustomUser.objects.filter(
            created_at__lte=deadline,
            is_verified=False
        )
        
        count = unverified_accounts.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('✅ No unverified accounts to delete'))
            return
        
        self.stdout.write(
            self.style.WARNING(
                f'\n⚠️  Found {count} unverified account(s) older than {days} days:'
            )
        )
        
        for user in unverified_accounts:
            days_since_creation = (timezone.now() - user.created_at).days
            self.stdout.write(
                f'   • {user.username} (created {days_since_creation} days ago on {user.created_at.date()})'
            )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\n📋 DRY RUN: These {count} account(s) would be deleted\n'
                    f'   Run without --dry-run to actually delete them'
                )
            )
        else:
            unverified_accounts.delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ Successfully deleted {count} unverified account(s)\n'
                )
            )
