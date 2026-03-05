import os
from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import KnowledgeFile

@receiver(post_delete, sender=KnowledgeFile)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes file from filesystem when corresponding `KnowledgeFile` object is deleted.
    """
    if instance.file:
        try:
            if os.path.isfile(instance.file.path):
                os.remove(instance.file.path)
        except Exception as e:
            # Log error or ignore if file doesn't exist
            print(f"Error deleting file: {e}")
