from django.core.management.base import BaseCommand
from datetime import timedelta
from django.utils.timezone import now
from ...models import Story  # Apne app ka naam replace karein

class Command(BaseCommand):
    help = "Delete all stories older than 24 hours"

    def handle(self, *args, **kwargs):
        old_stories = Story.objects.filter(created_at__lt=now() - timedelta(hours=24))
        count = old_stories.count()
        old_stories.delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {count} old stories."))
