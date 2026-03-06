import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'botman_backend.settings')
django.setup()

from accounts.models import User, Plan, Subscription

def main():
    # Create plans
    free_plan, _ = Plan.objects.get_or_create(name='Free', defaults={'bot_limit': 1})
    pro_plan, _ = Plan.objects.get_or_create(name='Pro', defaults={'bot_limit': 10})
    enterprise_plan, _ = Plan.objects.get_or_create(name='Enterprise', defaults={'bot_limit': 10000})

    # Assign plans to users
    for user in User.objects.all():
        if user.is_superuser or user.role == 'admin':
            Subscription.objects.get_or_create(user=user, defaults={'plan': enterprise_plan})
        else:
            Subscription.objects.get_or_create(user=user, defaults={'plan': free_plan})

if __name__ == '__main__':
    main()
