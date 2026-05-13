# Smart Job Portal — Project Documentation

## 1. Project Overview
The **Smart Job Portal** is a modern, AI-assisted platform designed to bridge the gap between job seekers and employers. Unlike traditional job boards, it introduces intelligent skill-matching algorithms, live interview preparation tools, and integrated scheduling, creating a frictionless hiring ecosystem.

This document serves as an educational breakdown of the architecture, features, and technologies used to build the platform.

---

## 2. Technology Stack
The project is built on a robust, scalable backend using Python and Django.

- **Backend Framework**: Django 5.x (Python 3)
- **Database**: 
  - *Development*: SQLite3 (lightweight, file-based)
  - *Production*: PostgreSQL (relational database mapped via `DATABASE_URL` on Railway)
- **Frontend**: HTML5, CSS3 (Custom Vanilla CSS design system without heavy frameworks), Django Template Engine.
- **APIs & Data Sourcing**: `requests`, `urllib`, `BeautifulSoup4` for web scraping and API consumption.
- **Deployment**: Railway (PaaS) with `gunicorn` for WSGI server management.

---

## 3. Core Architecture & Features

### A. Role-Based User Management
The system extends Django's standard `AbstractUser` to create a `CustomUser` model. This allows the application to differentiate between user types natively.
- **Seeker**: Can create profiles, upload resumes, take quizzes, and apply for jobs.
- **Employer**: Can post jobs, review applicants, and schedule interviews.
- **Admin/Staff**: Accesses the global dashboard to monitor platform health and manage data.

### B. Intelligent Skill Matching
When a seeker views a job or an employer views an applicant, the system calculates a **Skill Match Score**.
- **How it works**: The system tokenizes the `required_skills` of a job and the `skills` listed on the seeker's profile. It uses set intersection logic (`seeker_skills.intersection(job_skills)`) to calculate a mathematical percentage of alignment.
- **Impact**: Seekers only see "Recommended Jobs" that match their profile >0%, and employers see applicants sorted by highest match percentage.

### C. Live Interview Preparation & Assessment
Instead of static pages, the portal dynamically generates study materials based on the job's required skills.
- **Web Scraping**: Uses `BeautifulSoup4` to scrape real-world, skill-specific interview questions (e.g., Python, Django) live from InterviewBit.
- **Live MCQ Engine**: Connects to the **Open Trivia Database API** to generate real-time multiple-choice computer science questions.
- **Scoring & Persistence**: When a seeker submits the quiz, the server compares the inputs against the API's `correct_answer` keys. The score and user choices are saved in a `PrepAssessment` database model, allowing the platform to track candidate readiness.

### D. Interview Scheduling Pipeline
Employers can seamlessly transition an applicant from "Shortlisted" to "Interviewing".
- **In-App Notifications**: Scheduling an interview creates a `Notification` object linked to the seeker. This appears instantly on their dashboard.
- **Transactional Emails**: The system utilizes `django.core.mail.backends.smtp.EmailBackend` to send automated calendar invites and details directly to the candidate's registered email address using Gmail SMTP.

### E. External API Job Aggregation
To ensure the platform always has listings, the `external_jobs.py` module acts as an aggregator.
- **Sources**: 
  - *Remotive API* (Free, remote tech jobs)
  - *Arbeitnow API* (Free, global jobs)
  - *JSearch RapidAPI* (Global jobs mapped from LinkedIn/Indeed)
- **Mechanism**: The backend normalizes the JSON responses from these three distinct APIs into a standard internal Python dictionary format, allowing local database jobs and external API jobs to be rendered side-by-side in the same UI templates flawlessly.

---

## 4. Database Schema (Key Models)

1. **`CustomUser`**: Extends standard user with a `role` field.
2. **`SeekerProfile`**: Stores resume (FileField), skills, and bio. Links 1-to-1 with User.
3. **`Job`**: Stores title, description, skills, category, and links to the Employer (User).
4. **`Application`**: Links a Seeker to a Job. Tracks status (`applied`, `shortlisted`, `rejected`).
5. **`Interview`**: Links to an Application. Stores meeting links, dates, and times.
6. **`PrepAssessment`**: Stores JSON dictionaries of the seeker's quiz answers, score out of 5, and percentage.
7. **`Notification`**: A messaging model tracking unread alerts for seekers.
8. **`Feedback`**: Captures user reviews and a 1-5 star rating for the platform, which are subsequently rendered on the homepage.

---

## 5. Security & Best Practices
- **CSRF Protection**: All forms utilize Django's `{% csrf_token %}` to prevent Cross-Site Request Forgery.
- **Environment Variables**: Sensitive data (`SECRET_KEY`, `EMAIL_HOST_PASSWORD`, `RAPIDAPI_KEY`) are decoupled from the source code and managed via `.env` files locally and Railway variables in production.
- **Authentication Decorators**: Views are protected using `@login_required` and custom decorators like `@seeker_required` to prevent unauthorized URL access.

---

## 6. Deployment Workflow
The project is version-controlled via Git and hosted on GitHub.
It utilizes continuous deployment via **Railway**. 
- The `Procfile` tells Railway to run `gunicorn job_portal.wsgi` to serve the application.
- The `railway.toml` build configuration automatically runs `python manage.py migrate` during the deployment phase, ensuring the production PostgreSQL database schema is always up to date with the latest code models.
