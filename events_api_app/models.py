# events_api_app/models.py
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class UserProfile(models.Model):
    """
    Extends Django's built-in User with additional profile fields.
    OneToOne relation to User ensures a single profile per user.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=200, blank=True)
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        # Prefer a human-friendly full_name but fallback to username
        return self.full_name if self.full_name else self.user.username


class Event(models.Model):
    """
    Event model representing an event created by an organizer (User).
    invited_users provides a mechanism for private events access control.
    """
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_events')
    location = models.CharField(max_length=255)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_public = models.BooleanField(default=True)
    invited_users = models.ManyToManyField(User, related_name='invited_events', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['start_time']),
            models.Index(fields=['location']),
        ]

    def __str__(self):
        return f"{self.title} ({self.organizer.username})"


class RSVP(models.Model):
    """
    RSVP status for a user on a particular event.
    Unique constraint prevents duplicate RSVPs for the same event & user.
    """
    STATUS_GOING = 'Going'
    STATUS_MAYBE = 'Maybe'
    STATUS_NOT_GOING = 'Not Going'
    STATUS_CHOICES = [
        (STATUS_GOING, 'Going'),
        (STATUS_MAYBE, 'Maybe'),
        (STATUS_NOT_GOING, 'Not Going'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='rsvps')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rsvps')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('event', 'user')
        ordering = ['-created_at']

    def __str__(self):
        return f"RSVP: {self.user.username} -> {self.event.title} ({self.status})"


class Review(models.Model):
    """
    Review left by a user for an event. Rating is integer between 1 and 5.
    Unique constraint prevents a user leaving multiple reviews for same event.
    """
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('event', 'user')
        ordering = ['-created_at']

    def __str__(self):
        return f"Review: {self.user.username} -> {self.event.title} ({self.rating})"
