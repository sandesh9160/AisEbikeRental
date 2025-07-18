from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.custom_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('ebikes/', views.ebikes, name='ebikes'),
    path('submit-review/', views.submit_review, name='submit_review'),
    path('profile/update/', views.profile_update, name='profile_update'),
]

