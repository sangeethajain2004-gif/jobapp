"""
External Jobs Service
Fetches real job listings from free APIs:
  - Remotive API (no auth, remote jobs)
  - JSearch via RapidAPI (optional, Indian + global jobs)
"""
import urllib.request
import urllib.parse
import json
import os


def fetch_remotive_jobs(search='', limit=20):
    """Fetch remote tech jobs from Remotive API — completely free, no key needed."""
    try:
        params = {'limit': limit}
        if search:
            params['search'] = search
        url = 'https://remotive.com/api/remote-jobs?' + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={'User-Agent': 'SmartJobPortal/1.0'})
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode())
        jobs = []
        for j in data.get('jobs', []):
            jobs.append({
                'id': f"remotive_{j.get('id')}",
                'title': j.get('job_type', 'Full-time') and j.get('title', ''),
                'company': j.get('company_name', ''),
                'location': j.get('candidate_required_location') or 'Remote',
                'job_type': j.get('job_type', 'Full-time'),
                'category': j.get('category', 'IT'),
                'description': j.get('description', '')[:400] if j.get('description') else '',
                'skills': j.get('tags', []),
                'salary': j.get('salary', ''),
                'url': j.get('url', '#'),
                'posted_at': j.get('publication_date', ''),
                'source': 'Remotive',
                'is_external': True,
                'logo': j.get('company_logo', ''),
            })
        return jobs
    except Exception:
        return []


def fetch_jsearch_jobs(search='software developer india', rapidapi_key=None, limit=10):
    """Fetch jobs from JSearch API via RapidAPI (real LinkedIn/Indeed/Glassdoor jobs)."""
    key = rapidapi_key or os.environ.get('RAPIDAPI_KEY', '')
    if not key:
        return []
    try:
        query = urllib.parse.quote(search or 'developer india')
        url = f'https://jsearch.p.rapidapi.com/search?query={query}&num_pages=1&page=1'
        req = urllib.request.Request(url, headers={
            'X-RapidAPI-Key': key,
            'X-RapidAPI-Host': 'jsearch.p.rapidapi.com',
            'User-Agent': 'SmartJobPortal/1.0'
        })
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
        jobs = []
        for j in data.get('data', [])[:limit]:
            skills_raw = j.get('job_required_skills') or []
            jobs.append({
                'id': f"jsearch_{j.get('job_id', '')}",
                'title': j.get('job_title', ''),
                'company': j.get('employer_name', ''),
                'location': f"{j.get('job_city', '')} {j.get('job_country', '')}".strip() or 'India',
                'job_type': j.get('job_employment_type', 'Full-time').replace('_', ' ').title(),
                'category': 'IT',
                'description': (j.get('job_description') or '')[:400],
                'skills': skills_raw[:6] if skills_raw else [],
                'salary': '',
                'url': j.get('job_apply_link', '#'),
                'posted_at': j.get('job_posted_at_datetime_utc', ''),
                'source': j.get('job_publisher', 'JSearch'),
                'is_external': True,
                'logo': j.get('employer_logo', ''),
            })
        return jobs
    except Exception:
        return []


def fetch_arbeitnow_jobs(search='', limit=15):
    """Fetch jobs from Arbeitnow API — free, no auth, global remote jobs."""
    try:
        url = 'https://www.arbeitnow.com/api/job-board-api?page=1'
        req = urllib.request.Request(url, headers={'User-Agent': 'SmartJobPortal/1.0'})
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode())
        jobs = []
        results = data.get('data', [])
        if search:
            q = search.lower()
            results = [j for j in results if q in j.get('title', '').lower()
                       or q in j.get('description', '').lower()
                       or any(q in t.lower() for t in j.get('tags', []))]
        for j in results[:limit]:
            jobs.append({
                'id': f"arbeitnow_{j.get('slug', '')}",
                'title': j.get('title', ''),
                'company': j.get('company_name', ''),
                'location': j.get('location', 'Remote'),
                'job_type': 'Remote' if j.get('remote') else 'Full-time',
                'category': 'IT',
                'description': (j.get('description') or '')[:400],
                'skills': j.get('tags', [])[:6],
                'salary': '',
                'url': j.get('url', '#'),
                'posted_at': str(j.get('created_at', '')),
                'source': 'Arbeitnow',
                'is_external': True,
                'logo': '',
            })
        return jobs
    except Exception:
        return []


def get_external_jobs(search='', limit=24):
    """
    Aggregate jobs from all available sources.
    Returns a combined list of external job dicts.
    """
    all_jobs = []

    # Source 1: Remotive (remote tech jobs, always free)
    remotive = fetch_remotive_jobs(search=search, limit=limit // 2)
    all_jobs.extend(remotive)

    # Source 2: Arbeitnow (free global jobs, no auth)
    if len(all_jobs) < limit:
        arbeitnow = fetch_arbeitnow_jobs(search=search, limit=limit // 3)
        all_jobs.extend(arbeitnow)

    # Source 3: JSearch (optional RapidAPI key for Indian/global jobs)
    if len(all_jobs) < limit:
        query = f"{search} india" if search else "software developer india"
        jsearch = fetch_jsearch_jobs(search=query, limit=limit // 4)
        all_jobs.extend(jsearch)

    return all_jobs[:limit]
