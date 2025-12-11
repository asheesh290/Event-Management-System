# events_api_app/admin.py
from django.contrib import admin
from .models import UserProfile, Event, RSVP, Review

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'location')
    search_fields = ('user__username', 'full_name', 'location')

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'organizer', 'location', 'start_time', 'is_public')
    list_filter = ('is_public', 'location', 'start_time')
    search_fields = ('title', 'description', 'organizer__username')
    raw_id_fields = ('organizer',)
    filter_horizontal = ('invited_users',)

@admin.register(RSVP)
class RSVPAdmin(admin.ModelAdmin):
    list_display = ('id', 'event', 'user', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('event__title', 'user__username')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'event', 'user', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('event__title', 'user__username', 'comment')
