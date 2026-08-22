"""Live API test script."""
import httpx
from datetime import datetime, timedelta

BASE = "http://127.0.0.1:8080"
API = f"{BASE}/api/v1"
passed = 0
failed = 0


def test(name, resp, expected=None):
    global passed, failed
    ok = not expected or resp.status_code == expected
    tag = "PASS" if ok else "FAIL"
    print(f"[{tag}] {name} -> {resp.status_code}")
    if not ok:
        failed += 1
        print(f"  Expected {expected}: {resp.text[:200]}")
    else:
        passed += 1
    return ok


c = httpx.Client(timeout=30)

print("\n=== HEALTH CHECK ===")
r = c.get(f"{BASE}/health")
test("GET /health", r, 200)
r = c.get(f"{BASE}/")
test("GET /", r, 200)

print("\n=== AUTH ===")
sd = {"email": "test@example.com", "password": "pass123", "full_name": "Test User"}
r = c.post(f"{API}/auth/signup", json=sd)
test("POST /auth/signup", r, 201)
r = c.post(f"{API}/auth/signup", json=sd)
test("POST /auth/signup (dup)", r, 400)
r = c.post(f"{API}/auth/login", json={"email": "test@example.com", "password": "pass123"})
test("POST /auth/login", r, 200)
token = r.json()["access_token"]
h = {"Authorization": f"Bearer {token}"}
r = c.get(f"{API}/auth/me", headers=h)
test("GET /auth/me", r, 200)
r = c.get(f"{API}/auth/me")
test("GET /auth/me (no token)", r, 401)
r = c.post(f"{API}/auth/login", json={"email": "test@example.com", "password": "wrong"})
test("POST /auth/login (wrong)", r, 401)

print("\n=== RESUMES ===")
rb = b"John Doe - Software Engineer\nSkills: Python, JavaScript, React, SQL, Docker\nExperience: 5 years\nEducation: BS CS"
files = {"file": ("resume.txt", rb, "text/plain")}
r = c.post(f"{API}/resumes/", files=files, headers=h)
test("POST /resumes/ (upload)", r, 201)
resume_id = r.json()["resume_id"]
r = c.get(f"{API}/resumes/", headers=h)
test("GET /resumes/", r, 200)
files = {"file": ("x.exe", b"bad", "application/octet-stream")}
r = c.post(f"{API}/resumes/", files=files, headers=h)
test("POST /resumes/ (bad type)", r, 400)

print("\n=== JOBS ===")
jd = {
    "job_title": "Senior Python Developer",
    "company_name": "Google",
    "job_description": "Python, Django, REST APIs, PostgreSQL, Docker, cloud services. 5+ years exp.",
    "location": "Mountain View, CA",
}
r = c.post(f"{API}/jobs/", json=jd, headers=h)
test("POST /jobs/", r, 201)
job_id = r.json()["job_id"]
r = c.get(f"{API}/jobs/", headers=h)
test("GET /jobs/", r, 200)
r = c.get(f"{API}/jobs/{job_id}", headers=h)
test("GET /jobs/{id}", r, 200)
r = c.get(f"{API}/jobs/00000000-0000-0000-0000-000000000000", headers=h)
test("GET /jobs (not found)", r, 404)

print("\n=== APPLICATIONS + AI ===")
r = c.post(f"{API}/applications/", json={"job_id": job_id, "resume_id": resume_id}, headers=h)
test("POST /applications/", r, 201)
app = r.json()
app_id = app["application_id"]
print(f"  score: {app['relevance_score']}, status: {app['status']}")
r = c.post(f"{API}/applications/", json={"job_id": job_id, "resume_id": resume_id}, headers=h)
test("POST /applications/ (dup)", r, 400)
r = c.get(f"{API}/applications/", headers=h)
test("GET /applications/", r, 200)
r = c.get(f"{API}/applications/{app_id}", headers=h)
test("GET /applications/{id}", r, 200)
d = r.json()
print(f"  matched: {d.get('matched_skills')}")
print(f"  missing: {d.get('missing_skills')}")
print(f"  tips: {str(d.get('tailored_suggestions',''))[:80]}...")
r = c.patch(f"{API}/applications/{app_id}/status", json={"status": "interview", "notes": "Screen set"}, headers=h)
test("PATCH status -> interview", r, 200)
r = c.patch(f"{API}/applications/{app_id}/status", json={"status": "bad"}, headers=h)
test("PATCH status (invalid)", r, 400)
r = c.get(f"{API}/applications/{app_id}/history", headers=h)
test("GET /history", r, 200)
print(f"  transitions: {len(r.json())}")
r = c.patch(f"{API}/applications/{app_id}/status", json={"status": "offer", "notes": "Got it!"}, headers=h)
test("PATCH status -> offer", r, 200)
r = c.get(f"{API}/applications/{app_id}/history", headers=h)
test("GET /history (final)", r, 200)
print(f"  total: {len(r.json())}")
for x in r.json():
    print(f"    {x['status']}")

print("\n=== DASHBOARD ===")
r = c.get(f"{API}/dashboard/", headers=h)
test("GET /dashboard/", r, 200)
d = r.json()
print(f"  total: {d['total_applications']}")
print(f"  breakdown: {d['status_breakdown']}")
print(f"  avg_score: {d['average_relevance_score']}")

print("\n=== REMINDERS ===")
sched = (datetime.utcnow() + timedelta(days=3)).isoformat()
r = c.post(f"{API}/reminders/", json={
    "application_id": app_id, "reminder_type": "follow_up",
    "message": "Follow up on interview", "scheduled_at": sched,
}, headers=h)
test("POST /reminders/", r, 201)
rem_id = r.json()["reminder_id"]
r = c.get(f"{API}/reminders/", headers=h)
test("GET /reminders/", r, 200)
r = c.patch(f"{API}/reminders/{rem_id}/cancel", headers=h)
test("PATCH /reminders/cancel", r, 200)
print(f"  status after cancel: {r.json()['status']}")

print("\n" + "=" * 50)
print(f"RESULTS: {passed} passed, {failed} failed, {passed+failed} total")
print("=" * 50)
