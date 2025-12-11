# events_api_app/urls.py
from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import EventViewSet

router = DefaultRouter()
router.register(r'events', EventViewSet, basename='event')

urlpatterns = [
    path('', include(router.urls)),
]
