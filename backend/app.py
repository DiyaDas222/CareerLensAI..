from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask import make_response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None
try:
    from groq import Groq
except Exception:
    Groq = None
from io import BytesIO
import json
import os
import pdfplumber
from PIL import Image
import pytesseract
import datetime

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter

if load_dotenv:
    load_dotenv()

APP_VERSION = os.getenv("APP_VERSION", "2")

app = Flask(__name__)
# Allow CORS for deployed frontend calls.
# For production you should restrict origins, but this unblocks the current issue.
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=False)

app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey")

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "database.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
# Groq client is optional: app must still work without an API key
_groq_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=_groq_key) if (_groq_key and Groq) else None



class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


class ResumeReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    target_career = db.Column(db.String(100))
    score = db.Column(db.Integer)
    feedback = db.Column(db.Text)  # JSON string of analysis
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


# Check database and column consistency, recreate if missing columns
with app.app_context():
    try:
        db.create_all()
    except Exception:
        db.session.rollback()
        db.drop_all()
        db.create_all()

    # Ensure columns exist without dropping the entire database
    try:
        db.session.query(User.username).first()
    except Exception:
        # If User table/columns are corrupted, reset DB schema
        db.session.rollback()
        db.drop_all()
        db.create_all()


@app.route("/register", methods=["POST"])
def register():
    data = request.json or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"message": "Missing username or password"}), 400

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({"message": "User already exists"}), 409

    hashed_password = generate_password_hash(password)
    db.session.add(User(username=username, password=hashed_password))
    db.session.commit()

    return jsonify({"message": "Registration successful", "username": username})


@app.route("/login", methods=["POST"])
def login():
    data = request.json or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"message": "Invalid credentials"}), 400

    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
        return jsonify({"message": "Login successful", "username": username})

    return jsonify({"message": "Invalid credentials"}), 401


def extract_text_from_pdf(path: str) -> str:
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            extracted = page.extract_text() or ""
            text += extracted
    return text


def extract_text_from_image(path: str) -> str:
    try:
        img = Image.open(path)
        text = pytesseract.image_to_string(img)
        return text or ""
    except Exception as e:
        # Fallback if tesseract is not installed or raises an error
        print("Tesseract Error, OCR failed:", e)
        return ""


def analyze_resume_locally(text: str) -> dict:
    # Rule-based fallback/hybrid analyzer
    score = 40  # Base score for uploading any readable resume
    skills_found = []
    suggestions = []

    keywords = [
        "python", "java", "c++", "flask", "django", "react", "sql", 
        "machine learning", "ai", "html", "css", "javascript", "node",
        "aws", "docker", "kubernetes", "git", "linux", "c#", "data structures"
    ]

    for keyword in keywords:
        if keyword.lower() in text.lower():
            score += 3
            skills_found.append(keyword)

    word_count = len(text.split())
    if word_count > 300:
        score += 5
    else:
        suggestions.append("Resume content is too short (under 300 words). Add detail to your experience.")

    action_verbs = ["developed", "built", "created", "designed", "implemented", "optimized", "managed", "led"]
    verb_hits = 0
    for verb in action_verbs:
        if verb in text.lower():
            verb_hits += 1
            score += 1
    if verb_hits < 3:
        suggestions.append("Use more action verbs (e.g., 'developed', 'optimized') to describe achievements.")

    if "project" in text.lower():
        score += 5
    else:
        suggestions.append("Add a dedicated 'Projects' section to show practical application.")

    if "github" in text.lower() or "gitlab" in text.lower() or "bitbucket" in text.lower():
        score += 5
    else:
        suggestions.append("Include links to your GitHub profile or project portfolio.")

    if "certif" in text.lower():
        score += 3

    if "%" in text or "increase" in text.lower() or "reduced" in text.lower() or "saved" in text.lower():
        score += 5
    else:
        suggestions.append("Quantify your results (e.g., 'improved page load times by 20%').")

    score = min(score, 100)
    return {"score": score, "skills": skills_found, "suggestions": suggestions}


def generate_ai_feedback(text: str, target_career: str) -> str:
    # If GROQ is not configured, return a valid JSON payload so the frontend works.
    if not client:
        local = analyze_resume_locally(text)
        fallback = {
            "ats_score": local["score"],
            "career_match_score": 55,
            "placement_readiness_score": 50,
            "strengths": [
                "Resume text was extracted successfully.",
                "Some relevant skills/keywords were detected.",
                "Overall structure looks readable for ATS.".replace(".", ".")
            ],
            "weaknesses": [
                "AI career-specific analysis is unavailable because GROQ_API_KEY is not set.",
                "Add clearer job-relevant keywords and quantified impact.",
                "Ensure sections like Projects and Skills are explicitly labeled."
            ],
            "suggestions": [
                "Set GROQ_API_KEY in the backend environment to enable full AI analysis.",
                "Customize your resume for the target career using job-relevant keywords.",
                "Quantify achievements (percentages, metrics, outcomes)."
            ],
            "skills_found": local.get("skills", []),
            "missing_skills": ["Role-specific tools/technologies vary by target career"],
            "skills_to_improve": ["Tailor Skills section to {target_career}".format(target_career=target_career)],
            "hr_questions": ["Tell me about yourself.", "Why are you interested in this role?", "What is your biggest achievement?"] ,
            "technical_questions": ["Explain a project you built.", "How do you debug a challenging issue?", "What trade-offs do you consider in system design?"] ,
            "project_viva_questions": ["What technologies did you use and why?", "What challenges did you face?", "How did you measure success?"],
            "recommended_projects": [
                {
                    "title": "Target-Career Capstone",
                    "description": "Build a small end-to-end project aligned to {target_career}, document your decisions, and publish the repo.".format(target_career=target_career)
                }
            ],
            "career_roadmap": [
                "Step 1: Strengthen fundamentals aligned with {target_career}".format(target_career=target_career),
                "Step 2: Build 2-3 job-relevant projects and document impact",
                "Step 3: Practice interviews and optimize your resume" 
            ],
            "career_advice": ["Start with keywords + projects, then iterate based on ATS results.", "Keep bullets action-oriented and metric-backed.", "Align each project to a job requirement."],
            "resume_rewrite": [],
            "weekly_study_planner": {
                "Monday": "Resume keyword tailoring + ATS checks",
                "Tuesday": "Data structures / fundamentals",
                "Wednesday": "Build a job-relevant project",
                "Thursday": "Practice system/technical questions",
                "Friday": "Quantify outcomes + rewrite bullets",
                "Saturday": "Mock interview",
                "Sunday": "Review & plan next week"
            },
            "learning_resource_recommendations": [
                {"resource_type": "Practice Platforms", "title": "LeetCode / DSA practice", "link": "https://leetcode.com"},
                {"resource_type": "Documentation", "title": "MDN Web Docs / Tech fundamentals", "link": "https://developer.mozilla.org"}
            ]
        }
        return json.dumps(fallback)

    prompt = f"""
You are an expert career coach, ATS expert, and hiring manager.
Analyze the following resume specifically for the target career of "{target_career}".

Resume Text:
{text}

You must return a valid JSON object matching the following structure exactly. Do not wrap the JSON in markdown code blocks or add any extra text.

JSON Schema:
{{
  "ats_score": (integer between 0 and 100),
  "career_match_score": (integer between 0 and 100),
  "placement_readiness_score": (integer between 0 and 100),
  "strengths": [ "Strength 1", "Strength 2", "Strength 3" ],
  "weaknesses": [ "Weakness 1", "Weakness 2", "Weakness 3" ],
  "suggestions": [ "Suggestion 1", "Suggestion 2", "Suggestion 3" ],
  "skills_found": [ "Skill A", "Skill B" ],
  "missing_skills": [ "Skill X", "Skill Y" ],
  "skills_to_improve": [ "Improve Skill X", "Learn Skill Y" ],
  "hr_questions": [ "Question 1", "Question 2", "Question 3" ],
  "technical_questions": [ "Question 1", "Question 2", "Question 3" ],
  "project_viva_questions": [ "Question 1", "Question 2", "Question 3" ],
  "recommended_projects": [
     {{
       "title": "Project Title",
       "description": "Brief description of what the project is, what technologies to use, and why it helps."
     }}
  ],
  "career_roadmap": [
     "Step 1: Description",
     "Step 2: Description",
     "Step 3: Description"
  ],
  "career_advice": [ "Advice 1", "Advice 2", "Advice 3" ],
  "resume_rewrite": [
     {{
       "original": "Sample weak bullet point or section from the resume",
       "rewritten": "AI-optimized, high-impact action-oriented rewrite of that bullet point"
     }}
  ],
  "weekly_study_planner": {{
     "Monday": "Topic or activity",
     "Tuesday": "Topic or activity",
     "Wednesday": "Topic or activity",
     "Thursday": "Topic or activity",
     "Friday": "Topic or activity",
     "Saturday": "Topic or activity",
     "Sunday": "Topic or activity"
  }},
  "learning_resource_recommendations": [
     {{
       "resource_type": "YouTube Courses | Documentation | Articles | Practice Platforms",
       "title": "Title of the resource",
       "link": "URL to the resource"
     }}
  ]
}}
"""

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.3,
    )
    return completion.choices[0].message.content



@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "version": APP_VERSION}), 200


@app.route("/upload", methods=["POST"])
def upload_resume():
    try:
        if "resume" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["resume"]
        target_career = request.form.get("target_career", "Software Engineer")
        username = request.form.get("username", "demo_user")

        upload_folder = os.path.join(BASE_DIR, "uploads")
        os.makedirs(upload_folder, exist_ok=True)

        if not file.filename:
            return jsonify({"error": "Empty filename"}), 400

        filepath = os.path.join(upload_folder, file.filename)
        file.save(filepath)

        filename_lower = file.filename.lower()

        if filename_lower.endswith(".pdf"):
            text = extract_text_from_pdf(filepath)
        elif filename_lower.endswith((".png", ".jpg", ".jpeg")):
            text = extract_text_from_image(filepath)
            if not text.strip():
                return jsonify({
                    "error": "Tesseract OCR was unable to read the image, or is not installed on the server. Please upload a text-based PDF."
                }), 400
        else:
            return jsonify({
                "error": "Unsupported file type. Please upload a PDF or image (PNG/JPG/JPEG)."
            }), 400

        if not text.strip():
            return jsonify({"error": "Could not extract any text from the file. Try a clearer image or PDF."}), 422

        local_analysis = analyze_resume_locally(text)
        try:
            ai_feedback_str = generate_ai_feedback(text, target_career)
        except Exception:
            # Hard fallback so frontend never gets a 500 when GROQ fails
            ai_feedback_str = json.dumps({
                "ats_score": local_analysis["score"],
                "career_match_score": 55,
                "placement_readiness_score": 50,
                "strengths": ["Resume text extracted successfully."],
                "weaknesses": ["AI analysis failed; using local heuristic."],
                "suggestions": local_analysis.get("suggestions", []),
                "skills_found": local_analysis.get("skills", []),
                "missing_skills": ["Review role requirements"],
                "skills_to_improve": ["Customize skills to target role"],
                "hr_questions": [],
                "technical_questions": [],
                "project_viva_questions": [],
                "recommended_projects": [],
                "career_roadmap": [],
                "career_advice": [],
                "resume_rewrite": [],
                "weekly_study_planner": {},
                "learning_resource_recommendations": []
            })

        # Verify if feedback is valid JSON
        try:
            ai_data = json.loads(ai_feedback_str)
            # Use AI score as the definitive ATS score if present
            score = ai_data.get("ats_score", local_analysis["score"])
        except Exception:
            # Fallback
            score = local_analysis["score"]


        report = ResumeReport(
            username=username,
            target_career=target_career,
            score=score,
            feedback=ai_feedback_str
        )
        db.session.add(report)
        db.session.commit()

        return jsonify({
            "id": report.id,
            "score": score,
            "local_analysis": local_analysis,
            "ai_feedback": ai_feedback_str
        })

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        traceback.print_exc()
        return jsonify({"error": str(e), "exception_type": type(e).__name__, "trace": tb.splitlines()[-5:]}), 500


@app.route("/history", methods=["GET"])
def get_history():
    username = request.args.get("username", "demo_user")
    reports = ResumeReport.query.filter_by(username=username).order_by(ResumeReport.created_at.desc()).all()
    
    data = []
    for report in reports:
        data.append({
            "id": report.id,
            "username": report.username,
            "target_career": report.target_career,
            "score": report.score,
            "created_at": report.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "feedback": report.feedback
        })
    return jsonify(data)


@app.route("/generate-cover-letter", methods=["POST"])
def generate_cover_letter():
    try:
        data = request.json or {}
        report_id = data.get("report_id")
        username = data.get("username", "demo_user")
        company_name = data.get("company_name", "Dream Company")
        job_title = data.get("job_title", "Software Engineer")
        job_description = data.get("job_description", "")

        # Try to find a resume matching the report_id or the last analyzed report
        if report_id:
            report = ResumeReport.query.filter_by(id=report_id).first()
        else:
            report = ResumeReport.query.filter_by(username=username).order_by(ResumeReport.created_at.desc()).first()

        if not report:
            return jsonify({"error": "No resume history found. Please upload a resume first."}), 404

        # Extract context
        resume_summary = f"Applying for {job_title} at {company_name}.\n"
        try:
            feedback_json = json.loads(report.feedback)
            resume_summary += "Skills Found: " + ", ".join(feedback_json.get("skills_found", [])) + "\n"
            resume_summary += "Key Strengths: " + ", ".join(feedback_json.get("strengths", [])) + "\n"
        except:
            resume_summary += f"Raw analysis: {report.feedback[:400]}"

        prompt = f"""
You are an expert resume writer and career coach.
Generate a tailored, persuasive cover letter for a candidate applying for the role of "{job_title}" at "{company_name}".

Candidate's Background Summary:
{resume_summary}

Additional Job details:
{job_description}

Write a professional, compelling cover letter that highlights the most relevant skills, matches the target company, and follows standard corporate formats. Do not include placeholders (like [Date] or [Insert Name Here])—invent realistic details if needed.

You must return a valid JSON object matching this structure. Do not wrap the JSON in markdown code blocks.

JSON Schema:
{{
  "cover_letter": "The full text of the cover letter with proper spacing and paragraphs."
}}
"""
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.5,
        )
        return jsonify(json.loads(completion.choices[0].message.content))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/analyze-linkedin", methods=["POST"])
def analyze_linkedin():
    try:
        data = request.json or {}
        linkedin_text = data.get("linkedin_text", "")
        target_career = data.get("target_career", "Software Engineer")

        if not linkedin_text.strip():
            return jsonify({"error": "LinkedIn profile text cannot be empty."}), 400

        prompt = f"""
You are a LinkedIn profile optimization expert and branding specialist.
Analyze the following LinkedIn profile details to align them with the career goal of "{target_career}".

LinkedIn Profile Content:
{linkedin_text}

Evaluate the profile and return a valid JSON object matching this structure. Do not wrap the JSON in markdown code blocks.

JSON Schema:
{{
  "completeness_score": (integer between 0 and 100),
  "suggestions": [
     "Suggestion 1...",
     "Suggestion 2..."
  ],
  "optimized_headline": "A highly professional, attention-grabbing headline tailored for target career",
  "optimized_about": "A compelling, first-person LinkedIn About/Summary section highlighting skills and passion for the target career."
}}
"""
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.4,
        )
        return jsonify(json.loads(completion.choices[0].message.content))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/evaluate-mock-answer", methods=["POST"])
def evaluate_mock_answer():
    try:
        data = request.json or {}
        question = data.get("question", "")
        user_answer = data.get("user_answer", "")
        target_career = data.get("target_career", "Software Engineer")

        if not question or not user_answer:
            return jsonify({"error": "Question and answer are required."}), 400

        prompt = f"""
You are an expert interviewer evaluating a candidate for the role of "{target_career}".
Evaluate the candidate's answer to the following interview question.

Question:
{question}

Candidate's Answer:
{user_answer}

You must return a valid JSON object matching the following structure. Do not wrap the JSON in markdown code blocks or add any extra text.

JSON Schema:
{{
  "score": (integer between 0 and 100 representing answer quality),
  "feedback": "Constructive critique of what the candidate did well and what they can improve. Keep it detailed yet encouraging.",
  "suggested_answer": "An exemplary, high-scoring model answer that the candidate could use as a reference."
}}
"""
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        return jsonify(json.loads(completion.choices[0].message.content))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_readiness_level(score):
    try:
        score = int(score)
    except:
        return "Unknown"
    if score <= 40:
        return "Beginner (Needs significant skill building)"
    elif score <= 70:
        return "Developing (On the right track, needs projects)"
    elif score <= 85:
        return "Placement Ready (Competitive profile)"
    else:
        return "Highly Competitive (Industry-ready expert)"


def generate_pdf_from_report(report):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    # Custom colors
    primary_color = colors.HexColor("#1e3a8a")  # Deep Navy
    secondary_color = colors.HexColor("#0d9488")  # Teal
    text_color = colors.HexColor("#1f2937")  # Charcoal
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=primary_color,
        spaceAfter=10
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#4b5563"),
        spaceAfter=15
    )
    
    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=secondary_color,
        spaceBefore=12,
        spaceAfter=8,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=text_color,
        spaceAfter=5
    )
    
    bullet_style = ParagraphStyle(
        'DocBullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=text_color,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )
    
    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=11.5,
        textColor=colors.white
    )
    
    elements = []
    
    elements.append(Paragraph("CareerLens AI - Comprehensive Analysis Report", title_style))
    created_str = report.created_at.strftime("%Y-%m-%d %H:%M:%S") if report.created_at else "N/A"
    elements.append(Paragraph(f"<b>Candidate:</b> {report.username} | <b>Target Career:</b> {report.target_career or 'N/A'} | <b>Date:</b> {created_str}", subtitle_style))
    elements.append(Spacer(1, 10))
    
    try:
        data = json.loads(report.feedback)
        
        # Section 1: Overview
        elements.append(Paragraph("1. Performance Metrics Overview", h1_style))
        scores_data = [
            [Paragraph("<b>Metric</b>", table_header_style), Paragraph("<b>Score</b>", table_header_style), Paragraph("<b>Status / Level</b>", table_header_style)],
            [Paragraph("ATS Resume Score", body_style), Paragraph(f"{report.score}%", body_style), Paragraph("Evaluates formatting, structure & keywords", body_style)],
            [Paragraph("Career Match Score", body_style), Paragraph(f"{data.get('career_match_score', 'N/A')}%", body_style), Paragraph(f"Alignment with {report.target_career}", body_style)],
            [Paragraph("Placement Readiness Score", body_style), Paragraph(f"{data.get('placement_readiness_score', 'N/A')}%", body_style), Paragraph(get_readiness_level(data.get('placement_readiness_score', 0)), body_style)]
        ]
        
        t = Table(scores_data, colWidths=[140, 80, 300])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), primary_color),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 10))
        
        # Section 2: Strengths & Weaknesses
        elements.append(Paragraph("2. Resume Analysis & Feedback", h1_style))
        elements.append(Paragraph("<b>Strengths Detected:</b>", body_style))
        for s in data.get('strengths', []):
            elements.append(Paragraph(f"• {s}", bullet_style))
        elements.append(Spacer(1, 6))
        
        elements.append(Paragraph("<b>Areas of Weakness:</b>", body_style))
        for w in data.get('weaknesses', []):
            elements.append(Paragraph(f"• {w}", bullet_style))
        elements.append(Spacer(1, 6))
        
        elements.append(Paragraph("<b>Resume Suggestions:</b>", body_style))
        for sug in data.get('suggestions', []):
            elements.append(Paragraph(f"• {sug}", bullet_style))
        elements.append(Spacer(1, 10))
        
        # Section 3: Skill Gap Analysis
        elements.append(Paragraph("3. Skill Gap Analysis", h1_style))
        elements.append(Paragraph(f"Analyzing missing competencies for <b>{report.target_career}</b>:", body_style))
        
        skills_data = [
            [Paragraph("<b>Skills Detected</b>", table_header_style), Paragraph("<b>Missing Critical Skills</b>", table_header_style)],
            [
                Paragraph(", ".join(data.get('skills_found', [])) or "None detected", body_style),
                Paragraph(", ".join(data.get('missing_skills', [])) or "None identified", body_style)
            ]
        ]
        st = Table(skills_data, colWidths=[260, 260])
        st.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), secondary_color),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(st)
        elements.append(Spacer(1, 6))
        
        elements.append(Paragraph("<b>Skills to Improve:</b>", body_style))
        for sk in data.get('skills_to_improve', []):
            elements.append(Paragraph(f"• {sk}", bullet_style))
            
        elements.append(PageBreak())
        
        # Section 4: Interview Preparation
        elements.append(Paragraph("4. Interview Preparation Guide", h1_style))
        elements.append(Paragraph("<b>HR Interview Questions:</b>", body_style))
        for q in data.get('hr_questions', []):
            elements.append(Paragraph(f"• {q}", bullet_style))
        elements.append(Spacer(1, 6))
        
        elements.append(Paragraph("<b>Technical Interview Questions:</b>", body_style))
        for q in data.get('technical_questions', []):
            elements.append(Paragraph(f"• {q}", bullet_style))
        elements.append(Spacer(1, 6))
        
        elements.append(Paragraph("<b>Project Viva Questions:</b>", body_style))
        for q in data.get('project_viva_questions', []):
            elements.append(Paragraph(f"• {q}", bullet_style))
        elements.append(Spacer(1, 10))
        
        # Section 5: Roadmap & Recommended Projects
        elements.append(Paragraph("5. Step-by-Step Learning Roadmap", h1_style))
        for i, step in enumerate(data.get('career_roadmap', [])):
            elements.append(Paragraph(f"<b>{i+1}.</b> {step}", bullet_style))
        elements.append(Spacer(1, 8))
        
        elements.append(Paragraph("<b>Recommended Projects:</b>", body_style))
        for proj in data.get('recommended_projects', []):
            title = proj.get('title', 'Project') if isinstance(proj, dict) else 'Project'
            desc = proj.get('description', '') if isinstance(proj, dict) else str(proj)
            elements.append(Paragraph(f"• <b>{title}:</b> {desc}", bullet_style))
            
        elements.append(Spacer(1, 10))
        
        # Section 6: Planner & Resources
        elements.append(Paragraph("6. Weekly Study Planner", h1_style))
        planner = data.get('weekly_study_planner', {})
        if isinstance(planner, dict):
            for day, activity in planner.items():
                elements.append(Paragraph(f"<b>{day}:</b> {activity}", bullet_style))
        elements.append(Spacer(1, 8))
        
        elements.append(Paragraph("<b>Recommended Resources:</b>", body_style))
        for res in data.get('learning_resource_recommendations', []):
            if isinstance(res, dict):
                r_type = res.get('resource_type', 'Resource')
                title = res.get('title', 'Link')
                link = res.get('link', '#')
                elements.append(Paragraph(f"• [{r_type}] <b>{title}:</b> {link}", bullet_style))
            else:
                elements.append(Paragraph(f"• {res}", bullet_style))
                
    except Exception as e:
        elements.append(Paragraph("Raw AI Feedback (Error parsing details):", h1_style))
        elements.append(Paragraph(report.feedback.replace('\n', '<br/>'), body_style))
        
    doc.build(elements)
    return buffer


@app.route("/download-report")
def download_report():
    report_id = request.args.get("report_id")
    username = request.args.get("username", "demo_user")

    if report_id:
        report = ResumeReport.query.filter_by(id=report_id).first()
    else:
        report = ResumeReport.query.filter_by(username=username).order_by(ResumeReport.created_at.desc()).first()

    if not report:
        return jsonify({"error": "No report found. Please analyze a resume first."}), 404

    pdf_buffer = generate_pdf_from_report(report)
    pdf_buffer.seek(0)

    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"CareerLens_Report_{report.id}.pdf"
    )


if __name__ == "__main__":
    app.run(debug=True)
