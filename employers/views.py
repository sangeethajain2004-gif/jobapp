from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail
from django.utils import timezone
from django import forms
from .models import EmployerProfile
from jobs.models import Job, Application, Interview, Notification
from seekers.models import SeekerProfile


class EmployerProfileForm(forms.ModelForm):
    class Meta:
        model = EmployerProfile
        fields = ['company_name', 'industry', 'website', 'location', 'description', 'logo', 'employee_count', 'founded_year']
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Your Company Name'}),
            'industry': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Software, Finance'}),
            'website': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://yourcompany.com'}),
            'location': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'City, State'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 4, 'placeholder': 'Describe your company...'}),
            'employee_count': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. 50-200'}),
            'founded_year': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '2010'}),
        }


class JobPostForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['title', 'description', 'required_skills', 'location', 'salary_range', 'category', 'job_type']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Senior Python Developer'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 6, 'placeholder': 'Describe the role, responsibilities...'}),
            'required_skills': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Python, Django, REST API, SQL'}),
            'location': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Bangalore, Remote'}),
            'salary_range': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. 6-10 LPA'}),
            'category': forms.Select(attrs={'class': 'form-input'}),
            'job_type': forms.Select(attrs={'class': 'form-input'}),
        }


def employer_required(view_func):
    def wrapper(request, *args, **kwargs):
        # Not logged in → redirect to login and come back after
        if not request.user.is_authenticated:
            messages.warning(request, "Please login as an Employer to access this page.")
            from django.utils.http import urlencode
            login_url = '/accounts/login/?' + urlencode({'next': request.path})
            return redirect(login_url)
        # Logged in but as a seeker → show error, redirect to seeker dashboard
        if request.user.role != 'employer':
            messages.error(request, "⚠️ This page is only for Employers. You are logged in as a Job Seeker.")
            return redirect('seeker_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@employer_required
def employer_dashboard(request):
    profile, _ = EmployerProfile.objects.get_or_create(user=request.user)
    jobs = Job.objects.filter(employer=request.user)
    total_applications = Application.objects.filter(job__employer=request.user).count()
    shortlisted = Application.objects.filter(job__employer=request.user, status='shortlisted').count()
    return render(request, 'employers/dashboard.html', {
        'profile': profile,
        'jobs': jobs,
        'total_applications': total_applications,
        'shortlisted': shortlisted,
    })


@employer_required
def employer_profile(request):
    profile, _ = EmployerProfile.objects.get_or_create(user=request.user)
    form = EmployerProfileForm(request.POST or None, request.FILES or None, instance=profile)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Company profile updated!")
        return redirect('employer_dashboard')
    return render(request, 'employers/profile.html', {'form': form, 'profile': profile})


@employer_required
def post_job(request):
    form = JobPostForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        job = form.save(commit=False)
        job.employer = request.user
        job.save()
        messages.success(request, f"Job '{job.title}' posted successfully!")
        return redirect('employer_dashboard')
    return render(request, 'employers/post_job.html', {'form': form})


@employer_required
def edit_job(request, pk):
    job = get_object_or_404(Job, pk=pk, employer=request.user)
    form = JobPostForm(request.POST or None, instance=job)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Job updated successfully!")
        return redirect('employer_dashboard')
    return render(request, 'employers/post_job.html', {'form': form, 'editing': True, 'job': job})


@employer_required
def toggle_job(request, pk):
    job = get_object_or_404(Job, pk=pk, employer=request.user)
    job.is_active = not job.is_active
    job.save()
    status = "activated" if job.is_active else "deactivated"
    messages.success(request, f"Job '{job.title}' {status}.")
    return redirect('employer_dashboard')


@employer_required
def job_applicants(request, pk):
    job = get_object_or_404(Job, pk=pk, employer=request.user)
    applications = Application.objects.filter(job=job).select_related('seeker')

    # Attach match scores
    enriched = []
    for app in applications:
        try:
            profile = app.seeker.seeker_profile
            score = job.skill_match_score(profile.skills)
        except Exception:
            profile = None
            score = 0
        enriched.append({'app': app, 'profile': profile, 'score': score})

    enriched.sort(key=lambda x: x['score'], reverse=True)
    return render(request, 'employers/applicants.html', {
        'job': job,
        'enriched': enriched,
    })


@employer_required
def update_application_status(request, app_id):
    app = get_object_or_404(Application, pk=app_id, job__employer=request.user)
    new_status = request.POST.get('status')
    if new_status in ['applied', 'shortlisted', 'rejected']:
        app.status = new_status
        app.save()
        messages.success(request, f"Application status updated to '{new_status}'.")
    return redirect('job_applicants', pk=app.job.pk)


class InterviewForm(forms.ModelForm):
    scheduled_at = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M'],
        label='Interview Date & Time'
    )
    class Meta:
        model = Interview
        fields = ['scheduled_at', 'meeting_link', 'location', 'notes']
        widgets = {
            'meeting_link': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://meet.google.com/...'}),
            'location':     forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Office address or leave blank for virtual'}),
            'notes':        forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Any special instructions for the candidate...'}),
        }


@employer_required
def schedule_interview(request, app_id):
    application = get_object_or_404(Application, pk=app_id, job__employer=request.user)
    interview   = getattr(application, 'interview', None)
    form        = InterviewForm(request.POST or None, instance=interview)

    if request.method == 'POST' and form.is_valid():
        iv = form.save(commit=False)
        iv.application = application
        iv.save()

        seeker = application.seeker
        job    = application.job
        dt_str = iv.scheduled_at.strftime('%d %b %Y at %I:%M %p')

        # ── In-app notification ──
        Notification.objects.update_or_create(
            user=seeker,
            defaults={
                'message': f"📅 Interview scheduled for '{job.title}' on {dt_str}.",
                'link': '/seeker/dashboard/',
                'is_read': False,
            }
        )

        # ── Email notification ──
        email_body = (
            f"Hello {seeker.username},\n\n"
            f"Congratulations! {request.user.username} has scheduled an interview with you.\n\n"
            f"Job:          {job.title}\n"
            f"Date & Time:  {dt_str} (IST)\n"
            f"{f'Meeting Link: {iv.meeting_link}' if iv.meeting_link else f'Location: {iv.location}'}\n"
            f"{f'Notes: {iv.notes}' if iv.notes else ''}\n\n"
            f"Please be prepared and on time. Best of luck!\n\nSmartJobs Team"
        )
        try:
            send_mail(
                subject=f"Interview Scheduled: {job.title}",
                message=email_body,
                from_email=None,   # uses DEFAULT_FROM_EMAIL from settings
                recipient_list=[seeker.email],
                fail_silently=True,
            )
        except Exception:
            pass  # Don't crash if email fails

        messages.success(request, f"Interview scheduled and {seeker.username} has been notified!")
        return redirect('job_applicants', pk=job.pk)

    return render(request, 'employers/schedule_interview.html', {
        'form': form,
        'application': application,
        'existing': interview,
    })
