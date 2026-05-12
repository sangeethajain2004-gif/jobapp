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


@seeker_required
def prep_material(request, app_id):
    from django.shortcuts import get_object_or_404
    application = get_object_or_404(Application, pk=app_id, seeker=request.user)
    job = application.job
    skills = job.get_skills_list()
    
    # Generate generic prep material based on skills
    questions = []
    for skill in skills[:4]:
        questions.append(f"Explain the core concepts of {skill} and how you have used it in past projects.")
        questions.append(f"What are the most common challenges you face when working with {skill}, and how do you overcome them?")
    
    if not questions:
        questions = [
            "Tell me about yourself and your background.",
            "Why are you interested in this position?",
            "Can you describe a challenging project you worked on and how you handled it?",
            "Where do you see yourself in 5 years?"
        ]
        
    quiz = [
        {"q": f"Which of the following best describes your proficiency with {skills[0] if skills else 'the required tools'}?", "options": ["Beginner", "Intermediate", "Advanced", "Expert"]},
        {"q": "How do you handle tight deadlines?", "options": ["Prioritize tasks", "Ask for an extension", "Work overtime", "Delegate"]},
        {"q": "Describe your ideal work environment.", "options": ["Fully remote", "Hybrid", "In-office", "Flexible"]},
    ]

    return render(request, 'seekers/prep_material.html', {
        'application': application,
        'job': job,
        'questions': set(questions),  # Remove duplicates
        'quiz': quiz
    })
