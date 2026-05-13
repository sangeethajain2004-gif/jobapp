from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django import forms
import requests
import random
import html as html_lib
from bs4 import BeautifulSoup
from .models import SeekerProfile
from jobs.models import Job, Application, Notification, PrepAssessment


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

    # Upcoming interviews
    interviews = []
    for app in applications:
        iv = getattr(app, 'interview', None)
        if iv and iv.status == 'scheduled':
            interviews.append(iv)

    # Unread notifications
    notifications = Notification.objects.filter(user=request.user, is_read=False)

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

    shortlisted_count = applications.filter(status='shortlisted').count()

    return render(request, 'seekers/dashboard.html', {
        'profile': profile,
        'applications': applications,
        'recommended': recommended,
        'interviews': interviews,
        'notifications': notifications,
        'shortlisted_count': shortlisted_count,
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
def dismiss_notification(request, notif_id):
    notif = get_object_or_404(Notification, pk=notif_id, user=request.user)
    notif.is_read = True
    notif.save()
    return redirect('seeker_dashboard')


# ── Quiz answer key (correct answer index per question) ────────────────────
QUIZ_ANSWERS = {
    0: 2,  # Q1: "Advanced" is best answer
    1: 0,  # Q2: "Prioritize tasks" is best
    2: 2,  # Q3: Any is fine, but "In-office" used as baseline
}


def scrape_interview_questions(skill):
    """Scrape real interview questions from InterviewBit."""
    url = f'https://www.interviewbit.com/{skill.lower().replace(" ", "-")}-interview-questions/'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        response = requests.get(url, headers=headers, timeout=3)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            questions = []
            for h3 in soup.find_all('h3'):
                text = h3.get_text(strip=True)
                if text and '?' in text:
                    clean_text = text.split('. ', 1)[-1] if '. ' in text[:5] else text
                    questions.append(clean_text)
            return questions[:10]  # Return top 10
    except Exception:
        pass
    return []


def get_resource_links(skill):
    """Return curated resource links for a given skill."""
    slug = skill.strip().lower().replace(' ', '-')
    name = skill.strip().title()
    return [
        {'site': 'GeeksforGeeks',   'url': f'https://www.geeksforgeeks.org/{slug}/', 'icon': '📗'},
        {'site': 'InterviewBit',    'url': f'https://www.interviewbit.com/{slug}-interview-questions/', 'icon': '💡'},
        {'site': 'LeetCode',        'url': f'https://leetcode.com/tag/{slug}/', 'icon': '⚡'},
        {'site': 'YouTube Tutorial','url': f'https://www.youtube.com/results?search_query={slug}+tutorial+for+beginners', 'icon': '🎥'},
    ]


def fetch_mcq_questions(count=5):
    """
    Fetch real MCQ questions live from Open Trivia DB.
    Category 18 = Science: Computers — real tech interview-style questions.
    Always returns correct_answer alongside shuffled options.
    """
    try:
        url = f'https://opentdb.com/api.php?amount={count}&category=18&type=multiple'
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        data = resp.json()
        if data.get('response_code') == 0:
            quiz = []
            for item in data['results']:
                question = html_lib.unescape(item['question'])
                correct  = html_lib.unescape(item['correct_answer'])
                options  = [html_lib.unescape(o) for o in item['incorrect_answers']] + [correct]
                random.shuffle(options)
                quiz.append({
                    'q':       question,
                    'options': options,
                    'correct': correct,
                })
            return quiz
    except Exception:
        pass
    return []  # fallback handled in the view


FALLBACK_QUIZ = [
    {'q': 'What does CPU stand for?',
     'options': ['Central Process Unit', 'Central Processing Unit', 'Core Processing Unit', 'Computer Processing Unit'],
     'correct': 'Central Processing Unit'},
    {'q': 'Which data structure uses LIFO order?',
     'options': ['Queue', 'Stack', 'Linked List', 'Tree'],
     'correct': 'Stack'},
    {'q': 'What does HTTP stand for?',
     'options': ['HyperText Transfer Protocol', 'High Transfer Text Protocol', 'HyperText Transmission Protocol', 'Host Transfer Text Protocol'],
     'correct': 'HyperText Transfer Protocol'},
    {'q': 'Which of the following is NOT a programming language?',
     'options': ['Python', 'Java', 'HTML', 'Kotlin'],
     'correct': 'HTML'},
    {'q': 'What does SQL stand for?',
     'options': ['Structured Query Language', 'Simple Query Language', 'Structured Question Language', 'Sequential Query Language'],
     'correct': 'Structured Query Language'},
]


@seeker_required
def prep_material(request, app_id):
    application = get_object_or_404(Application, pk=app_id, seeker=request.user)
    job = application.job
    skills = job.get_skills_list()

    # ── Real-time interview questions (scraped from InterviewBit) ──
    questions = []
    for skill in skills[:3]:  # scrape up to 3 skills
        scraped = scrape_interview_questions(skill)
        if scraped:
            questions.extend(scraped)
        else:
            questions.append(f"Explain the core concepts of {skill} and how you've used it in past projects.")
            questions.append(f"What are the most common challenges with {skill}, and how do you overcome them?")
            questions.append(f"Can you walk us through a real project where you applied {skill}?")
            questions.append(f"How do you stay up to date with the latest developments in {skill}?")
    if not questions:
        questions = [
            "Tell me about yourself and your background.",
            "Why are you interested in this position?",
            "Describe a challenging project and how you handled it.",
            "Where do you see yourself in 5 years?",
        ]
    unique_qs = list(dict.fromkeys(questions))[:10]  # cap at 10 questions

    # ── Real-time MCQ quiz from Open Trivia DB API ──
    # Fetch fresh questions and store in session so submit can score correctly
    session_key = f'quiz_{app_id}'
    quiz = fetch_mcq_questions(count=5)
    if not quiz:
        quiz = FALLBACK_QUIZ  # offline fallback
    request.session[session_key] = quiz  # store for scoring

    # ── Resource links ──
    resources = {}
    for skill in skills[:3]:
        resources[skill.title()] = get_resource_links(skill)

    prior = getattr(application, 'assessment', None)

    return render(request, 'seekers/prep_material.html', {
        'application': application,
        'job': job,
        'questions': unique_qs,
        'quiz': quiz,
        'resources': resources,
        'prior': prior,
    })


@seeker_required
def submit_assessment(request, app_id):
    if request.method != 'POST':
        return redirect('prep_material', app_id=app_id)

    application = get_object_or_404(Application, pk=app_id, seeker=request.user)
    job = application.job

    # Retrieve the exact same quiz that was shown (stored in session)
    session_key = f'quiz_{app_id}'
    quiz = request.session.get(session_key, FALLBACK_QUIZ)

    score = 0
    answers = {}  # {question_index: selected_answer_text}
    for i, item in enumerate(quiz):
        selected = request.POST.get(f'q{i}')
        answers[str(i)] = selected or ''
        if selected and selected == item['correct']:
            score += 1

    assessment, _ = PrepAssessment.objects.update_or_create(
        application=application,
        defaults={'score': score, 'total': len(quiz), 'answers': answers}
    )

    # Build results list for template — no custom filters needed
    results = []
    for i, item in enumerate(quiz):
        selected = answers.get(str(i), '')
        results.append({
            'q':         item['q'],
            'options':   item['options'],
            'correct':   item['correct'],
            'selected':  selected,
            'is_correct': selected == item['correct'],
        })

    return render(request, 'seekers/assessment_result.html', {
        'assessment': assessment,
        'job': job,
        'results': results,
        'app_id': app_id,
    })
