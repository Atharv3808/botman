from django.contrib.auth.models import AbstractUser
from django.db import models

class Plan(models.Model):
    name = models.CharField(max_length=50, unique=True)
    bot_limit = models.IntegerField(default=1)

    def __str__(self):
        return self.name

class User(AbstractUser):
    ROLE_CHOICES = (
        ('user', 'User'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')

class Subscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.user.username} - {self.plan.name}'