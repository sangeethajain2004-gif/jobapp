from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django import forms
from .models import SeekerProfile
from jobs.models import Job, Application


class SeekerProfileForm(forms.ModelForm):
    class Meta:
        model = SeekerProfile
        fields = ['full_name', 'phone', 'location', 'skills', 'experience_years',
                  'education', 'bio', 'resume', 'profile_photo', 'linkedin', 'github']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Your full name'}),
            'phone': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+91 9876543210'}),
            'location': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'City, State'}),
            'skills': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Python, Django, React, SQL'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'education': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'B.Tech CSE, XYZ University'}),
            'bio': forms.Textarea(attrs={'class': 'form-input', 'rows': 4, 'placeholder': 'Tell employers about yourself...'}),
            'linkedin': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://linkedin.com/in/...'}),
            'github': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://github.com/...'}),
        }


def seeker_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'seeker':
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


@seeker_required
def seeker_dashboard(request):
    profile, _ = SeekerProfile.objects.get_or_create(user=request.user)
    applications = Application.objects.filter(seeker=request.user).select_related('job')

    # Smart job recommendations
    all_jobs = Job.objects.filter(is_active=True)
    applied_job_ids = applications.values_list('job_id', flat=True)
    recommended = []
    for job in all_jobs:
        if job.id not in applied_job_ids:
            score = job.skill_match_score(profile.skills)
            if score > 0:
                recommended.append((job, score))
    recommended.sort(key=lambda x: x[1], reverse=True)
    recommended = recommended[:6]

    return render(request, 'seekers/dashboard.html', {
        'profile': profile,
        'applications': applications,
        'recommended': recommended,
    })


@seeker_required
def seeker_profile(request):
    profile, _ = SeekerProfile.objects.get_or_create(user=request.user)
    form = SeekerProfileForm(request.POST or None, request.FILES or None, instance=profile)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('seeker_dashboard')
    return render(request, 'seekers/profile.html', {'form': form, 'profile': profile})
