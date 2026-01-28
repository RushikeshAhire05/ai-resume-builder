# app.py
import streamlit as st
from resume_generator import generate_bullets, score_keywords
from fpdf import FPDF

st.set_page_config(page_title="AI Resume & Portfolio Builder", layout="centered")
st.title("AI Resume & Portfolio Builder (Prototype)")

st.markdown("Enter your details below and click **Generate Resume**. The app will create short, achievement-based bullets and let you download a PDF.")

with st.form("profile_form"):
    name = st.text_input("Full name")
    email = st.text_input("Email (optional)")
    summary = st.text_area("Brief summary / objective (1-2 lines)", height=80)
    education = st.text_area("Education (one line each)", height=80)
    skills_raw = st.text_input("Skills (comma separated, e.g. Python, SQL, Docker)")
    skills = [s.strip() for s in skills_raw.split(",") if s.strip()]
    st.subheader("One sample project (optional)")
    project_title = st.text_input("Project title")
    project_description = st.text_area("Project description (short)", height=80)
    target_role = st.text_input("Target role (e.g., Data Engineer, Web Developer)")
    job_description = st.text_area("Paste a job description to check keyword match (optional)", height=120)

    submitted = st.form_submit_button("Generate Resume")

if submitted:
    profile = {
        "summary": summary,
        "education": education,
        "skills": skills,
        "projects": []
    }
    if project_title and project_description:
        profile["projects"].append({"title": project_title, "description": project_description})

    with st.spinner("Generating resume bullets..."):
        bullets = generate_bullets(profile, target_role or "General")

    st.subheader("Generated Resume Points")
    for b in bullets:
        st.write("•", b)

    if job_description:
        score = score_keywords(bullets, job_description)
        if score is not None:
            st.info(f"Approximate keyword match score: {score}%")

    # Resume preview
    st.subheader("Resume Preview")
    st.markdown(f"**{name or 'Your Name'}**  \n{email or ''}")
    if summary:
        st.markdown(f"**Summary**  \n{summary}")
    if education:
        st.markdown(f"**Education**  \n{education}")
    if skills:
        st.markdown(f"**Skills**  \n{', '.join(skills)}")
    if profile.get("projects"):
        st.markdown("**Projects**")
        for p in profile["projects"]:
            st.markdown(f"- **{p['title']}** — {p['description']}")
    st.markdown("**Experience / Achievements**")
    for b in bullets:
        st.markdown(f"- {b}")

    # Create PDF in-memory and offer download
    def build_pdf_bytes(name_str, email_str, summary_str, education_str, skills_list, projects_list, bullets_list):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", style="B", size=14)
        pdf.cell(0, 8, txt=name_str or "Name", ln=1)
        if email_str:
            pdf.set_font("Arial", size=10)
            pdf.cell(0, 6, txt=email_str, ln=1)
        pdf.ln(4)
        if summary_str:
            pdf.set_font("Arial", style="B", size=11)
            pdf.cell(0, 6, txt="Summary", ln=1)
            pdf.set_font("Arial", size=10)
            pdf.multi_cell(0, 6, txt=summary_str)
            pdf.ln(2)
        if education_str:
            pdf.set_font("Arial", style="B", size=11)
            pdf.cell(0, 6, txt="Education", ln=1)
            pdf.set_font("Arial", size=10)
            for line in education_str.splitlines():
                pdf.multi_cell(0, 6, txt=line)
            pdf.ln(2)
        if skills_list:
            pdf.set_font("Arial", style="B", size=11)
            pdf.cell(0, 6, txt="Skills", ln=1)
            pdf.set_font("Arial", size=10)
            pdf.multi_cell(0, 6, txt=", ".join(skills_list))
            pdf.ln(2)
        if projects_list:
            pdf.set_font("Arial", style="B", size=11)
            pdf.cell(0, 6, txt="Projects", ln=1)
            pdf.set_font("Arial", size=10)
            for p in projects_list:
                pdf.multi_cell(0, 6, txt=f"{p.get('title','Project')} — {p.get('description','')}")
            pdf.ln(2)
        if bullets_list:
            pdf.set_font("Arial", style="B", size=11)
            pdf.cell(0, 6, txt="Experience / Achievements", ln=1)
            pdf.set_font("Arial", size=10)
            for b in bullets_list:
                pdf.multi_cell(0, 6, txt=f"• {b}")
        # Return bytes
        pdf_str = pdf.output(dest='S')  # returns a str (bytes-like)
        if isinstance(pdf_str, str):
            pdf_bytes = pdf_str.encode('latin-1')  # FPDF uses latin-1 encoding
        else:
            pdf_bytes = pdf_str
        return pdf_bytes

    pdf_bytes = build_pdf_bytes(name, email, summary, education, skills, profile.get("projects", []), bullets)
    filename = (name.replace(" ", "_") if name else "resume") + ".pdf"
    st.download_button("Download Resume (PDF)", data=pdf_bytes, file_name=filename, mime="application/pdf")
