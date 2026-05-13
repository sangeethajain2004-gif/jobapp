from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.seeker_dashboard, name='seeker_dashboard'),
    path('profile/', views.seeker_profile, name='seeker_profile'),
    path('prep-material/<int:app_id>/', views.prep_material, name='prep_material'),
    path('prep-material/<int:app_id>/submit/', views.submit_assessment, name='submit_assessment'),
    path('notification/<int:notif_id>/dismiss/', views.dismiss_notification, name='dismiss_notification'),
]
