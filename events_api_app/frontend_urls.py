# events_api_app/frontend_urls.py
from django.urls import path
from . import frontend_views

urlpatterns = [
    path('', frontend_views.events_list_view, name='events_list'),
    path('create/', frontend_views.create_event_view, name='events_create'),   # new
    path('<int:event_id>/', frontend_views.event_detail_view, name='events_detail'),
    path('<int:event_id>/rsvp/', frontend_views.rsvp_create_or_update, name='events_rsvp'),
    path('<int:event_id>/review/', frontend_views.post_review, name='events_review'),
]
