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


class Interview(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    application  = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='interview')
    scheduled_at = models.DateTimeField()
    meeting_link = models.URLField(blank=True, help_text='Google Meet / Zoom link')
    location     = models.CharField(max_length=200, blank=True, help_text='Physical location if applicable')
    notes        = models.TextField(blank=True)
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    created_at   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Interview: {self.application} @ {self.scheduled_at:%d %b %Y %H:%M}"


class Notification(models.Model):
    user       = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    message    = models.TextField()
    link       = models.CharField(max_length=300, blank=True)
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message[:40]}"


class PrepAssessment(models.Model):
    application  = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='assessment')
    score        = models.IntegerField(default=0)
    total        = models.IntegerField(default=0)
    answers      = models.JSONField(default=dict)
    completed_at = models.DateTimeField(auto_now_add=True)

    @property
    def percentage(self):
        if self.total == 0:
            return 0
        return int((self.score / self.total) * 100)

    @property
    def band(self):
        pct = self.percentage
        if pct >= 71:
            return ('Interview Ready! 🚀', 'success')
        elif pct >= 41:
            return ('On Track 👍', 'primary')
        else:
            return ('Needs More Practice 📖', 'warning')

    def __str__(self):
        return f"Assessment for {self.application} — {self.percentage}%"


class Feedback(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='feedbacks')
    rating = models.IntegerField(default=5, help_text="Rating out of 5")
    review = models.TextField()
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.rating}/5"
