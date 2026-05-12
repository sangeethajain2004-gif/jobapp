from django.urls import path
from . import views

urlpatterns = [
    path('register/seeker/', views.register_seeker, name='register_seeker'),
    path('register/employer/', views.register_employer, name='register_employer'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
]
