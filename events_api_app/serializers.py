# events_api_app/serializers.py
from django.contrib.auth.models import User
from rest_framework import serializers
from .models import UserProfile, Event, RSVP, Review


class UserSerializer(serializers.ModelSerializer):
    """Lightweight user representation used across API responses."""
    class Meta:
        model = User
        fields = ("id", "username", "email")


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for the UserProfile that extends Django's User."""
    user = UserSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = ("id", "user", "full_name", "bio", "location", "profile_picture")


class EventSerializer(serializers.ModelSerializer):
    """
    Event serializer:
      - organizer is read-only and set by the view (perform_create)
      - invited_users accepts a list of user IDs
      - created_at / updated_at are read-only
    """
    organizer = UserSerializer(read_only=True)
    invited_users = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.all(),
        required=False,
        write_only=False
    )

    class Meta:
        model = Event
        fields = (
            "id",
            "title",
            "description",
            "organizer",
            "location",
            "start_time",
            "end_time",
            "is_public",
            "invited_users",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at", "organizer")

    def validate(self, data):
        """
        Ensure start_time < end_time when both provided. Handles partial updates.
        """
        # For update operations, instance may exist
        instance = getattr(self, "instance", None)

        start = data.get("start_time", getattr(instance, "start_time", None) if instance else None)
        end = data.get("end_time", getattr(instance, "end_time", None) if instance else None)

        if start and end and start >= end:
            raise serializers.ValidationError({"start_time": "start_time must be before end_time."})
        return data

    def create(self, validated_data):
        invited = validated_data.pop("invited_users", [])
        event = super().create(validated_data)
        if invited:
            event.invited_users.set(invited)
        return event

    def update(self, instance, validated_data):
        invited = validated_data.pop("invited_users", None)
        instance = super().update(instance, validated_data)
        if invited is not None:
            instance.invited_users.set(invited)
        return instance


class RSVPSerializer(serializers.ModelSerializer):
    """
    RSVP Serializer:
      - user is read-only (set by view)
      - event: primary key
      - status must be one of RSVP.STATUS_CHOICES
    """
    user = UserSerializer(read_only=True)
    event = serializers.PrimaryKeyRelatedField(queryset=Event.objects.all())

    class Meta:
        model = RSVP
        fields = ("id", "event", "user", "status", "created_at")
        read_only_fields = ("id", "user", "created_at")

    def validate_status(self, value):
        allowed = [choice[0] for choice in getattr(RSVP, "STATUS_CHOICES", [])]
        if value not in allowed:
            raise serializers.ValidationError(f"Invalid status. Allowed values: {allowed}")
        return value


class ReviewSerializer(serializers.ModelSerializer):
    """
    Review serializer:
      - user is read-only (set by view)
      - event: primary key
      - rating must be an integer between 1 and 5
    """
    user = UserSerializer(read_only=True)
    event = serializers.PrimaryKeyRelatedField(queryset=Event.objects.all())

    class Meta:
        model = Review
        fields = ("id", "event", "user", "rating", "comment", "created_at")
        read_only_fields = ("id", "user", "created_at")

    def validate_rating(self, value):
        if not isinstance(value, int):
            try:
                value = int(value)
            except Exception:
                raise serializers.ValidationError("Rating must be an integer.")
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value
