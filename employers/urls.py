from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.employer_dashboard, name='employer_dashboard'),
    path('profile/', views.employer_profile, name='employer_profile'),
    path('post-job/', views.post_job, name='post_job'),
    path('edit-job/<int:pk>/', views.edit_job, name='edit_job'),
    path('toggle-job/<int:pk>/', views.toggle_job, name='toggle_job'),
    path('jobs/<int:pk>/applicants/', views.job_applicants, name='job_applicants'),
    path('application/<int:app_id>/status/', views.update_application_status, name='update_application_status'),
]
