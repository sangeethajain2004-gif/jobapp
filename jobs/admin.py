from django.contrib import admin
from .models import Job, Application

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['title', 'employer', 'category', 'job_type', 'location', 'is_active', 'posted_at']
    list_filter = ['category', 'job_type', 'is_active']
    search_fields = ['title', 'required_skills']

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['seeker', 'job', 'status', 'applied_at']
    list_filter = ['status']
