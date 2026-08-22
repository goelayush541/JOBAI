import json
import random
from app.config import get_settings

settings = get_settings()


class GeminiService:
    async def analyze_resume_job_fit(
        self, resume_text: str, job_description: str
    ) -> dict:
        if not settings.GCP_PROJECT_ID:
            return self._mock_analysis(resume_text, job_description)

        import google.cloud.aiplatform as aiplatform
        from vertexai.generative_models import GenerationConfig, GenerativeModel

        aiplatform.init(project=settings.GCP_PROJECT_ID, region=settings.GCP_REGION)
        model = GenerativeModel(settings.VERTEX_AI_MODEL)
        generation_config = GenerationConfig(
            temperature=0.2, top_p=0.8, top_k=40, max_output_tokens=2048,
        )

        prompt = (
            "You are an expert career advisor and ATS "
            "(Applicant Tracking System) specialist.\n\n"
            "Analyze the following resume against the job description and provide:\n\n"
            "1. A relevance score from 0 to 100 (how well the resume matches the job)\n"
            "2. A list of skills/requirements found in both the resume and job "
            "description (matched_skills)\n"
            "3. A list of skills/requirements from the job description NOT found "
            "in the resume (missing_skills)\n"
            "4. Tailored suggestions to improve the resume for this specific job\n\n"
            "Respond in strict JSON format:\n"
            '{{\n'
            '    "relevance_score": <number 0-100>,\n'
            '    "matched_skills": [<list of matched skills/keywords>],\n'
            '    "missing_skills": [<list of missing skills/keywords>],\n'
            '    "tailored_suggestions": "<paragraph of actionable suggestions>"\n'
            '}}\n\n'
            "--- RESUME ---\n"
            f"{resume_text}\n\n"
            "--- JOB DESCRIPTION ---\n"
            f"{job_description}\n"
        )

        response = model.generate_content(prompt, generation_config=generation_config)
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        return json.loads(text)

    def _mock_analysis(self, resume_text: str, job_description: str) -> dict:
        resume_words = set(resume_text.lower().split())
        job_words = set(job_description.lower().split())
        common = resume_words & job_words
        score = min(100, max(20, len(common) * 3 + random.randint(10, 30)))

        tech_skills = [
            "python", "javascript", "react", "node", "sql", "aws",
            "docker", "kubernetes", "git", "api", "rest", "graphql",
            "html", "css", "typescript", "java", "go", "rust",
            "machine learning", "data analysis", "agile", "scrum",
        ]
        matched = [s for s in tech_skills if s in resume_text.lower()][:5]
        missing = [s for s in tech_skills if s in job_description.lower() and s not in resume_text.lower()][:3]

        return {
            "relevance_score": score,
            "matched_skills": matched or ["communication", "problem solving"],
            "missing_skills": missing or ["leadership", "cloud architecture"],
            "tailored_suggestions": (
                "Consider adding more specific technical keywords from the job description "
                "to your resume. Highlight quantifiable achievements and tailor your "
                "summary section to align with the role requirements."
            ),
        }


gemini_service = GeminiService()
