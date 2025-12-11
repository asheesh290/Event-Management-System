# events_api_app/signals.py
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UserProfile

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Create a UserProfile when a new User is created.
    On subsequent saves, ensure the related profile is saved too.
    """
    if created:
        UserProfile.objects.create(user=instance)
    else:
        # If profile exists, save it to trigger any signals; if not, create one
        try:
            instance.profile.save()
        except UserProfile.DoesNotExist:
            UserProfile.objects.create(user=instance)
