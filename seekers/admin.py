from django.contrib import admin
from .models import SeekerProfile

@admin.register(SeekerProfile)
class SeekerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'full_name', 'location', 'experience_years', 'updated_at']
    search_fields = ['full_name', 'skills']
