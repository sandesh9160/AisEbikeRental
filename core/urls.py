from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.custom_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('ebikes/', views.ebikes, name='ebikes'),
    path('favorites/', views.my_favorites, name='my_favorites'),
    path('favorites/toggle/<int:ebike_id>/', views.toggle_favorite, name='toggle_favorite'),
    path('submit-review/', views.submit_review, name='submit_review'),
    path('profile/update/', views.profile_update, name='profile_update'),
    # Password Reset URLs
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset/done/', views.password_reset_done, name='password_reset_done'),
    path('password-reset/confirm/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
]

