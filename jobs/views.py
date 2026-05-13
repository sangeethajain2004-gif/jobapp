from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.db.models import Q
from .models import Job, Application, Feedback
from .external_jobs import get_external_jobs
from accounts.models import CustomUser


def home(request):
    # Show a mix of local jobs + external jobs on homepage
    local_jobs = list(Job.objects.filter(is_active=True)[:4])
    external = get_external_jobs(limit=6) if len(local_jobs) < 6 else []
    recent_jobs = local_jobs + external
    total_jobs = Job.objects.filter(is_active=True).count()
    total_seekers = CustomUser.objects.filter(role='seeker').count()
    total_employers = CustomUser.objects.filter(role='employer').count()
    
    # Testimonials
    feedbacks = Feedback.objects.filter(is_approved=True)[:5]

    return render(request, 'home.html', {
        'recent_jobs': recent_jobs,
        'total_jobs': total_jobs + 5000,   # Add external count estimate
        'total_seekers': total_seekers,
        'total_employers': total_employers,
        'feedbacks': feedbacks,
    })


def job_list(request):
    query = request.GET.get('q', '')
    location = request.GET.get('location', '')
    category = request.GET.get('category', '')
    job_type = request.GET.get('job_type', '')

    # --- Local jobs from our DB ---
    local_jobs = Job.objects.filter(is_active=True)
    if query:
        local_jobs = local_jobs.filter(
            Q(title__icontains=query) | Q(required_skills__icontains=query) | Q(description__icontains=query)
        )
    if location:
        local_jobs = local_jobs.filter(location__icontains=location)
    if category:
        local_jobs = local_jobs.filter(category=category)
    if job_type:
        local_jobs = local_jobs.filter(job_type=job_type)

    # --- External jobs from APIs ---
    search_term = query or location or category or 'developer'
    external_jobs = get_external_jobs(search=search_term, limit=24)

    # Filter external by location/type if specified
    if location:
        external_jobs = [j for j in external_jobs if location.lower() in j['location'].lower()]
    if job_type:
        external_jobs = [j for j in external_jobs if job_type.lower() in j['job_type'].lower()]

    return render(request, 'jobs/list.html', {
        'jobs': local_jobs,
        'external_jobs': external_jobs,
        'query': query,
        'location': location,
        'category': category,
        'job_type': job_type,
        'categories': Job.CATEGORY_CHOICES,
        'job_types': Job.JOB_TYPE_CHOICES,
        'total_count': local_jobs.count() + len(external_jobs),
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


def about(request):
    return render(request, 'pages/about.html')


def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        email_body = f"Message from {name} ({email}):\n\n{message}"
        
        try:
            send_mail(
                subject=f"Contact Form: {subject}",
                message=email_body,
                from_email=None,
                recipient_list=[email], # Sending a copy to them, and maybe to admin. For now just standard usage
                fail_silently=True,
            )
            messages.success(request, "Thank you! Your message has been sent successfully.")
        except Exception:
            messages.error(request, "There was an error sending your message. Please try again later.")
        
        return redirect('contact')
        
    return render(request, 'pages/contact.html')


@login_required
def submit_feedback(request):
    if request.method == 'POST':
        rating = request.POST.get('rating')
        review = request.POST.get('review')
        
        if rating and review:
            Feedback.objects.create(
                user=request.user,
                rating=int(rating),
                review=review,
                is_approved=True # Auto-approve for demo
            )
            messages.success(request, "Thank you for your review! It has been posted to our homepage.")
            return redirect('home')
        else:
            messages.error(request, "Please provide both a rating and a review.")
            
    return render(request, 'pages/feedback.html')
