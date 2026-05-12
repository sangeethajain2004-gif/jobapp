from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from .forms import SeekerRegistrationForm, EmployerRegistrationForm, LoginForm


def register_seeker(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = SeekerRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f"Welcome, {user.username}! Your seeker account is ready.")
        return redirect('seeker_dashboard')
    return render(request, 'accounts/register_seeker.html', {'form': form})


def register_employer(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = EmployerRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f"Welcome! Your employer account is ready.")
        return redirect('employer_dashboard')
    return render(request, 'accounts/register_employer.html', {'form': form})


def user_login(request):
    if request.user.is_authenticated:
        # Already logged in — redirect by role
        if request.user.role == 'employer':
            return redirect('employer_dashboard')
        return redirect('seeker_dashboard')

    next_url = request.GET.get('next') or request.POST.get('next', '')
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        messages.success(request, f"Welcome back, {user.username}!")
        # Redirect to next URL if present and safe, else role-based dashboard
        if next_url and next_url.startswith('/'):
            return redirect(next_url)
        if user.is_seeker():
            return redirect('seeker_dashboard')
        else:
            return redirect('employer_dashboard')
    return render(request, 'accounts/login.html', {'form': form, 'next': next_url})


def user_logout(request):
    logout(request)
    messages.info(request, "You've been logged out.")
    return redirect('home')


from django.contrib.admin.views.decorators import staff_member_required
from jobs.models import Job, Application
from accounts.models import CustomUser

@staff_member_required
def admin_dashboard(request):
    total_seekers = CustomUser.objects.filter(role='seeker').count()
    total_employers = CustomUser.objects.filter(role='employer').count()
    total_jobs = Job.objects.count()
    total_applications = Application.objects.count()
    
    recent_employers = CustomUser.objects.filter(role='employer').order_by('-date_joined')[:5]
    recent_seekers = CustomUser.objects.filter(role='seeker').order_by('-date_joined')[:5]
    recent_jobs = Job.objects.order_by('-posted_at')[:5]

    return render(request, 'accounts/admin_dashboard.html', {
        'total_seekers': total_seekers,
        'total_employers': total_employers,
        'total_jobs': total_jobs,
        'total_applications': total_applications,
        'recent_employers': recent_employers,
        'recent_seekers': recent_seekers,
        'recent_jobs': recent_jobs,
    })
