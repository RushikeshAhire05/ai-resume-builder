# resume_generator.py
import re
from transformers import pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

# Lazy initialize generator so import is fast
GEN_PIPE = None

def get_generator(model_name="distilgpt2"):
    global GEN_PIPE
    if GEN_PIPE is None:
        # Will download model the first time it runs (may take a while)
        GEN_PIPE = pipeline("text-generation", model=model_name, tokenizer=model_name)
    return GEN_PIPE

def normalize_text(s: str):
    return re.sub(r"\s+", " ", (s or "").strip())

def make_prompt(profile: dict, role: str):
    parts = []
    if profile.get("summary"):
        parts.append(f"Summary: {profile.get('summary')}")
    if profile.get("education"):
        parts.append(f"Education: {profile.get('education')}")
    if profile.get("skills"):
        if isinstance(profile.get("skills"), (list, tuple)):
            skills_txt = ", ".join(profile.get("skills"))
        else:
            skills_txt = profile.get("skills")
        parts.append(f"Skills: {skills_txt}")
    if profile.get("projects"):
        for p in profile.get("projects"):
            parts.append(f"Project: {p.get('title','Untitled')} - {p.get('description','')}")
    context = " | ".join(parts)
    prompt = (
        f"Write 4 concise, achievement-focused resume bullets for a candidate targeting the role: {role}.\n"
        f"Use action verbs and prefer measurable outcomes where possible. Base bullets on the following profile: {context}\n\nBullets:\n-"
    )
    return normalize_text(prompt)

def extract_bullets_from_text(text):
    # Try to find lines starting with '-' or numbered lines, else split heuristically.
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # if bullet char present
        if line.startswith("-") or line.startswith("*") or re.match(r"^\d+\.", line):
            cleaned = re.sub(r"^[-*\d\.\s]+", "", line).strip()
            lines.append(cleaned)
        else:
            # if looks like a sentence and not the prompt rest
            if len(line) > 20 and len(lines) < 6:
                lines.append(line)
    # final cleanup
    bullets = []
    for l in lines:
        l = l.strip()
        if len(l) > 10:
            if not l.endswith("."):
                l = l + "."
            bullets.append(l)
    return bullets

def fallback_bullets(profile, role):
    bullets = []
    skills = profile.get("skills", [])
    if isinstance(skills, (list, tuple)):
        skills_sample = ", ".join(skills[:5])
    else:
        skills_sample = skills
    if skills_sample:
        bullets.append(f"Proficient in {skills_sample}, applied knowledge to academic projects and coursework.")
    if profile.get("projects"):
        for p in profile.get("projects")[:3]:
            title = p.get("title", "Project")
            desc = p.get("description", "")[:120]
            bullets.append(f"{title}: {desc}.")
    if not bullets:
        bullets.append(f"Motivated candidate targeting {role} with strong academic background.")
    return bullets[:4]

def generate_bullets(profile: dict, role: str, model_name="distilgpt2"):
    """
    Returns list of up to 4 bullets (strings).
    Uses a transformer model; falls back to simple bullets if generation fails.
    """
    try:
        prompt = make_prompt(profile, role or "General")
        gen = get_generator(model_name=model_name)
        out = gen(prompt, max_length=180, do_sample=True, top_k=50, top_p=0.9, num_return_sequences=1)
        text = out[0].get("generated_text", "")
        # If generator repeated prompt, try to cut after "Bullets:"
        if "Bullets:" in text:
            after = text.split("Bullets:")[-1]
        else:
            after = text
        bullets = extract_bullets_from_text(after)
        if not bullets:
            bullets = fallback_bullets(profile, role)
        return bullets[:4]
    except Exception as e:
        # If any error (no internet, model error), return fallback bullets
        print("Generation error, using fallback bullets:", e)
        return fallback_bullets(profile, role)

def score_keywords(bullets, job_description):
    """
    Returns a simple percent-like score (0-100) showing average TF-IDF similarity.
    If job_description empty, returns None.
    """
    if not job_description or not bullets:
        return None
    docs = [job_description] + bullets
    try:
        tf = TfidfVectorizer().fit_transform(docs)
        job_vec = tf[0]
        sims = (tf[1:] @ job_vec.T).toarray().flatten()
        avg = float(np.mean(sims))
        return round(avg * 100, 1)
    except Exception as e:
        print("Scoring error:", e)
        return None

if __name__ == "__main__":
    # Quick local test
    prof = {
        "summary": "Final-year CS student interested in data and backend roles.",
        "education": "B.Tech Computer Science",
        "skills": ["Python", "SQL", "Pandas", "Docker"],
        "projects": [{"title": "Student Portal", "description": "Built a portal to manage student projects using Flask and SQLite."}]
    }
    print(generate_bullets(prof, "Data Engineer"))
    print(score_keywords(["Experience building ETL pipelines."], "Looking for data engineer with Python and SQL."))
