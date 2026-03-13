from django.core.management.base import BaseCommand
from dramatiq import cli

class Command(BaseCommand):
    help = 'Runs a dramatiq worker.'

    def handle(self, *args, **options):
        cli.main()
