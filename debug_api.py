import httpx, json

BASE = "http://127.0.0.1:8080"
API = f"{BASE}/api/v1"
c = httpx.Client(timeout=30)

# Signup + Login
c.post(f"{API}/auth/signup", json={"email":"t1@t.com","password":"p","full_name":"T"})
r = c.post(f"{API}/auth/login", json={"email":"t1@t.com","password":"p"})
h = {"Authorization": f"Bearer {r.json()['access_token']}"}

# Upload resume
files = {"file": ("resume.txt", b"Python React Docker SQL experience", "text/plain")}
r = c.post(f"{API}/resumes/", files=files, headers=h)
resume_id = r.json()["resume_id"]

# Create job
r = c.post(f"{API}/jobs/", json={"job_title":"Dev","company_name":"Co","job_description":"Python Docker"}, headers=h)
job_id = r.json()["job_id"]

# Create application - capture full error
r = c.post(f"{API}/applications/", json={"job_id": job_id, "resume_id": resume_id}, headers=h)
print(f"Status: {r.status_code}")
print(f"Headers: {dict(r.headers)}")
print(f"Body: {r.text}")
