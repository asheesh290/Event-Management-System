# events_api_app/permissions.py
from rest_framework import permissions


class IsOrganizerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow the organizer of an event to edit/delete it.
    Read-only requests are allowed for any user (further visibility is enforced elsewhere).
    """
    def has_object_permission(self, request, view, obj):
        # SAFE methods are allowed for everyone (subject to other checks in views)
        if request.method in permissions.SAFE_METHODS:
            return True
        # Only the organizer can perform unsafe (write) operations
        return hasattr(obj, "organizer") and obj.organizer == request.user


class IsInvitedOrPublic(permissions.BasePermission):
    """
    Permission that allows access to an Event object only if:
      - the event is public, OR
      - the user is the organizer, OR
      - the user is in invited_users.
    This is intended for object retrieval (GET) of private events.
    """
    def has_object_permission(self, request, view, obj):
        # If event is public, allow
        if getattr(obj, "is_public", False):
            return True

        # Must be an authenticated user for private events
        user = request.user
        if not user or not user.is_authenticated:
            return False

        # Organizer always allowed
        if getattr(obj, "organizer", None) == user:
            return True

        # invited_users is expected to be a ManyToMany relation
        try:
            return user in obj.invited_users.all()
        except Exception:
            # If invited_users does not exist or fails, deny access
            return False
