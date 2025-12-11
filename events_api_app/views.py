# events_api_app/views.py
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend

from .models import Event, RSVP, Review
from .serializers import EventSerializer, RSVPSerializer, ReviewSerializer
from .permissions import IsOrganizerOrReadOnly, IsInvitedOrPublic


class EventViewSet(viewsets.ModelViewSet):
    """
    Event endpoints:
      - POST /api/events/         -> create (auth required)
      - GET  /api/events/         -> list (public + invited/organized for authenticated users)
      - GET  /api/events/{id}/    -> retrieve (private events only visible to invited/organizer)
      - PUT  /api/events/{id}/    -> update (only organizer)
      - DELETE /api/events/{id}/  -> delete (only organizer)

    Additional actions:
      - POST   /api/events/{id}/rsvp/                  -> create or update caller's RSVP
      - PATCH  /api/events/{id}/rsvp/{user_id}/        -> update RSVP for a user (owner or organizer)
      - GET/POST /api/events/{id}/reviews/             -> list/create reviews
    """
    queryset = Event.objects.all().order_by('-created_at')
    serializer_class = EventSerializer
    # Default permission stack: allow reads for everyone (subject to queryset),
    # but only organizer may edit/delete (enforced by IsOrganizerOrReadOnly).
    permission_classes = [IsAuthenticatedOrReadOnly, IsOrganizerOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['location', 'is_public']
    search_fields = ['title', 'location', 'organizer__username']

    def get_permissions(self):
        """
        Return permission instances based on action:
          - retrieve: require event to be public or caller to be invited/organizer
          - create: require authenticated user
          - other actions: use default permission_classes
        """
        if self.action == 'retrieve':
            return [IsInvitedOrPublic()]
        if self.action == 'create':
            return [IsAuthenticated()]
        return super().get_permissions()

    def get_queryset(self):
        """
        For list view, return:
          - if anonymous: only public events
          - if authenticated: public events OR private events where user is invited OR organizer
        For other actions (retrieve, update, destroy), default queryset is used.
        """
        user = getattr(self.request, "user", None)
        qs = Event.objects.all().order_by('-created_at')
        if self.action == 'list' or self.action is None:
            if user and user.is_authenticated:
                return qs.filter(Q(is_public=True) | Q(invited_users=user) | Q(organizer=user)).distinct()
            return qs.filter(is_public=True)
        return qs

    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated], url_path='rsvp')
    def rsvp(self, request, pk=None):
        """
        POST /api/events/{id}/rsvp/
        Body: { "status": "Going" }
        Creates or updates the authenticated user's RSVP for the event.
        """
        event = self.get_object()

        # Check visibility: if private, only invited or organizer can RSVP
        if not event.is_public and request.user != event.organizer and request.user not in event.invited_users.all():
            return Response({'detail': 'You are not allowed to RSVP to this private event.'}, status=status.HTTP_403_FORBIDDEN)

        data = request.data.copy()
        data['event'] = event.id
        serializer = RSVPSerializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        status_value = serializer.validated_data['status']
        rsvp_obj, created = RSVP.objects.update_or_create(
            event=event, user=request.user,
            defaults={'status': status_value}
        )
        out = RSVPSerializer(rsvp_obj)
        return Response(out.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated], url_path=r'rsvp/(?P<user_id>\d+)')
    def update_rsvp(self, request, pk=None, user_id=None):
        """
        PATCH /api/events/{id}/rsvp/{user_id}/
        Only the RSVP owner or the event organizer can update the RSVP status.
        Body: {"status": "Maybe"}
        """
        event = self.get_object()
        rsvp = get_object_or_404(RSVP, event=event, user__id=user_id)

        # permission: only organizer or the user themself
        if request.user != rsvp.user and request.user != event.organizer:
            return Response({'detail': 'Not allowed to update this RSVP.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = RSVPSerializer(rsvp, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get', 'post'], permission_classes=[IsAuthenticatedOrReadOnly], url_path='reviews')
    def reviews(self, request, pk=None):
        """
        GET  /api/events/{id}/reviews/  -> list reviews (paginated)
        POST /api/events/{id}/reviews/  -> create a review (authenticated only)
        """
        event = self.get_object()

        if request.method == 'POST':
            # Optional: restrict reviews to attendees/invitees. Here we allow any authenticated user.
            data = request.data.copy()
            data['event'] = event.id
            serializer = ReviewSerializer(data=data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            reviews_qs = event.reviews.all().order_by('-created_at')
            page = self.paginate_queryset(reviews_qs)
            if page is not None:
                serializer = ReviewSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            serializer = ReviewSerializer(reviews_qs, many=True)
            return Response(serializer.data)
