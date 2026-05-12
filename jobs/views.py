from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Job, Application
from accounts.models import CustomUser


def home(request):
    recent_jobs = Job.objects.filter(is_active=True)[:6]
    total_jobs = Job.objects.filter(is_active=True).count()
    total_seekers = CustomUser.objects.filter(role='seeker').count()
    total_employers = CustomUser.objects.filter(role='employer').count()
    return render(request, 'home.html', {
        'recent_jobs': recent_jobs,
        'total_jobs': total_jobs,
        'total_seekers': total_seekers,
        'total_employers': total_employers,
    })


def job_list(request):
    jobs = Job.objects.filter(is_active=True)
    query = request.GET.get('q', '')
    location = request.GET.get('location', '')
    category = request.GET.get('category', '')
    job_type = request.GET.get('job_type', '')

    if query:
        jobs = jobs.filter(Q(title__icontains=query) | Q(required_skills__icontains=query) | Q(description__icontains=query))
    if location:
        jobs = jobs.filter(location__icontains=location)
    if category:
        jobs = jobs.filter(category=category)
    if job_type:
        jobs = jobs.filter(job_type=job_type)

    return render(request, 'jobs/list.html', {
        'jobs': jobs,
        'query': query,
        'location': location,
        'category': category,
        'job_type': job_type,
        'categories': Job.CATEGORY_CHOICES,
        'job_types': Job.JOB_TYPE_CHOICES,
    })


def job_detail(request, pk):
    job = get_object_or_404(Job, pk=pk, is_active=True)
    already_applied = False
    if request.user.is_authenticated and request.user.role == 'seeker':
        already_applied = Application.objects.filter(job=job, seeker=request.user).exists()
    return render(request, 'jobs/detail.html', {
        'job': job,
        'already_applied': already_applied,
        'skills_list': job.get_skills_list(),
    })


@login_required
def apply_job(request, pk):
    if request.user.role != 'seeker':
        messages.error(request, "Only job seekers can apply for jobs.")
        return redirect('job_detail', pk=pk)

    job = get_object_or_404(Job, pk=pk, is_active=True)
    if Application.objects.filter(job=job, seeker=request.user).exists():
        messages.warning(request, "You have already applied for this job.")
        return redirect('job_detail', pk=pk)

    cover_note = request.POST.get('cover_note', '')
    Application.objects.create(job=job, seeker=request.user, cover_note=cover_note)
    messages.success(request, f"Successfully applied for '{job.title}'!")
    return redirect('seeker_dashboard')
