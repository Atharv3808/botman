from django.core.management.base import BaseCommand
from accounts.models import User, Plan, Subscription

class Command(BaseCommand):
    help = 'Seeds the database with plans and assigns them to users.'

    def handle(self, *args, **options):
        # Create plans
        free_plan, _ = Plan.objects.get_or_create(name='Free', defaults={'bot_limit': 1})
        pro_plan, _ = Plan.objects.get_or_create(name='Pro', defaults={'bot_limit': 10})
        enterprise_plan, _ = Plan.objects.get_or_create(name='Enterprise', defaults={'bot_limit': 10000})

        # Assign plans to users
        for user in User.objects.all():
            if user.is_superuser or user.role == 'admin':
                Subscription.objects.get_or_create(user=user, defaults={'plan': enterprise_plan})
                self.stdout.write(self.style.SUCCESS(f'Assigned Enterprise plan to {user.username}'))
            else:
                Subscription.objects.get_or_create(user=user, defaults={'plan': free_plan})
                self.stdout.write(self.style.SUCCESS(f'Assigned Free plan to {user.username}'))
