from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from jobs import views as job_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', job_views.home, name='home'),
    path('accounts/', include('accounts.urls')),
    path('jobs/', include('jobs.urls')),
    path('seeker/', include('seekers.urls')),
    path('employer/', include('employers.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
