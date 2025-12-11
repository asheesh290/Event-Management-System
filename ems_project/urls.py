# ems_project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

# JWT views if available (optional)
try:
    from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
    jwt_available = True
except Exception:
    jwt_available = False

# Import profile view from our frontend views
from events_api_app import frontend_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Frontend events (list & detail)
    path('events/', include('events_api_app.frontend_urls')),

    # Profile page served by our frontend views
    path('accounts/profile/', frontend_views.profile_view, name='profile'),

    # --- Authentication views (explicit) ---
    # Login (renders registration/login.html)
    path(
        'accounts/login/',
        auth_views.LoginView.as_view(template_name='registration/login.html'),
        name='login'
    ),

    # Logout: use next_page so LogoutView always redirects to login
    path(
        'accounts/logout/',
        auth_views.LogoutView.as_view(next_page='/accounts/login/'),
        name='logout'
    ),

    # Password change (requires login)
    path(
        'accounts/password_change/',
        auth_views.PasswordChangeView.as_view(template_name='registration/password_change_form.html'),
        name='password_change'
    ),
    path(
        'accounts/password_change/done/',
        auth_views.PasswordChangeDoneView.as_view(template_name='registration/password_change_done.html'),
        name='password_change_done'
    ),

    # Password reset (password reset flow)
    path(
        'accounts/password_reset/',
        auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'),
        name='password_reset'
    ),
    path(
        'accounts/password_reset/done/',
        auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'),
        name='password_reset_done'
    ),
    path(
        'accounts/reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'),
        name='password_reset_confirm'
    ),
    path(
        'accounts/reset/done/',
        auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'),
        name='password_reset_complete'
    ),
    # --- end auth views ---

    # API endpoints
    path('api/', include('events_api_app.urls')),
]

# Add JWT endpoints only if simplejwt is available
if jwt_available:
    urlpatterns += [
        path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
        path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    ]

# Serve media in DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
