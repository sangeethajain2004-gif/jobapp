from django.db import models
from accounts.models import CustomUser


class Job(models.Model):
    CATEGORY_CHOICES = [
        ('IT', 'Information Technology'),
        ('Finance', 'Finance & Accounting'),
        ('Marketing', 'Marketing & Sales'),
        ('Design', 'Design & Creative'),
        ('Healthcare', 'Healthcare'),
        ('Education', 'Education'),
        ('Engineering', 'Engineering'),
        ('HR', 'Human Resources'),
        ('Other', 'Other'),
    ]
    JOB_TYPE_CHOICES = [
        ('Full-time', 'Full-time'),
        ('Part-time', 'Part-time'),
        ('Remote', 'Remote'),
        ('Internship', 'Internship'),
        ('Contract', 'Contract'),
    ]

    employer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='posted_jobs')
    title = models.CharField(max_length=200)
    description = models.TextField()
    required_skills = models.TextField(help_text='Comma-separated skills e.g. Python, Django, SQL')
    location = models.CharField(max_length=150)
    salary_range = models.CharField(max_length=100, blank=True, help_text='e.g. 4-6 LPA')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='IT')
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES, default='Full-time')
    is_active = models.BooleanField(default=True)
    posted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-posted_at']

    def __str__(self):
        return f"{self.title} at {self.employer.username}"

    def get_skills_list(self):
        return [s.strip().lower() for s in self.required_skills.split(',') if s.strip()]

    def skill_match_score(self, seeker_skills_text):
        """Returns match percentage between job skills and seeker skills."""
        if not seeker_skills_text:
            return 0
        seeker_skills = set(s.strip().lower() for s in seeker_skills_text.split(',') if s.strip())
        job_skills = set(self.get_skills_list())
        if not job_skills:
            return 0
        matched = seeker_skills.intersection(job_skills)
        return int((len(matched) / len(job_skills)) * 100)


class Application(models.Model):
    STATUS_CHOICES = [
        ('applied', 'Applied'),
        ('shortlisted', 'Shortlisted'),
        ('rejected', 'Rejected'),
    ]

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    seeker = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='applications')
    applied_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='applied')
    cover_note = models.TextField(blank=True, help_text='Optional note to employer')

    class Meta:
        unique_together = ('job', 'seeker')
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.seeker.username} → {self.job.title}"
