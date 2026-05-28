from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

import PyPDF2
import docx

from reportlab.pdfgen import canvas

import jwt
import datetime

import random
import smtplib

from email.mime.text import MIMEText

app = Flask(__name__)

app.secret_key = "careerlens_secret"

CORS(app)

# DATABASE

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

db = SQLAlchemy(app)

latest_result = {}

otp_storage = {}

# =========================
# DATABASE TABLES
# =========================

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(100),
        unique=True
    )

    password = db.Column(
        db.String(200)
    )


class Resume(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    score = db.Column(db.Integer)

    level = db.Column(db.String(50))

    skills = db.Column(db.Text)

    suggestions = db.Column(db.Text)


# CREATE DATABASE

with app.app_context():

    db.create_all()


# =========================
# SEND OTP EMAIL
# =========================

def send_otp_email(receiver_email, otp):

    sender_email = "diyadasam@gmail.com"

    sender_password = "abcdefghijklmnop"

    subject = "CareerLens AI OTP Verification"

    body = f"Your OTP is: {otp}"

    msg = MIMEText(body)

    msg['Subject'] = subject

    msg['From'] = sender_email

    msg['To'] = receiver_email

    server = smtplib.SMTP(
        'smtp.gmail.com',
        587
    )

    server.starttls()

    server.login(
        sender_email,
        sender_password
    )

    server.send_message(msg)

    server.quit()


# =========================
# PDF TEXT EXTRACTION
# =========================

def extract_text_from_pdf(file):

    reader = PyPDF2.PdfReader(file)

    text = ""

    for page in reader.pages:

        if page.extract_text():

            text += page.extract_text()

    return text


# =========================
# DOCX TEXT EXTRACTION
# =========================

def extract_text_from_docx(file):

    doc = docx.Document(file)

    text = ""

    for para in doc.paragraphs:

        text += para.text + "\n"

    return text


# =========================
# RESUME ANALYSIS
# =========================

def analyze_resume(text):

    score = 0

    suggestions = []

    skills = [
        "Python",
        "Java",
        "C++",
        "SQL",
        "HTML",
        "CSS",
        "JavaScript",
        "React",
        "Flask",
        "Git",
        "Machine Learning"
    ]

    found_skills = []

    for skill in skills:

        if skill.lower() in text.lower():

            found_skills.append(skill)

            score += 8

    important_sections = [
        "project",
        "education",
        "skills",
        "experience"
    ]

    for section in important_sections:

        if section not in text.lower():

            suggestions.append(
                f"Add {section} section"
            )

        else:

            score += 5

    if "internship" not in text.lower():

        suggestions.append(
            "Add internship experience"
        )

    else:

        score += 10

    if "github" in text.lower():

        score += 10

    if score > 100:

        score = 100

    if score >= 80:

        level = "Excellent"

    elif score >= 60:

        level = "Good"

    elif score >= 40:

        level = "Average"

    else:

        level = "Needs Improvement"

    return {

        "score": score,

        "level": level,

        "skills_found": found_skills,

        "suggestions": suggestions
    }


# =========================
# HOME ROUTE
# =========================

@app.route('/')

def home():

    return "CareerLens AI Running!"


# =========================
# REGISTER
# =========================

@app.route('/register', methods=['POST'])

def register():

    data = request.json

    username = data['username']

    password = data['password']

    existing_user = User.query.filter_by(
        username=username
    ).first()

    if existing_user:

        return jsonify({
            "message": "User already exists"
        })

    hashed_password = generate_password_hash(
        password
    )

    new_user = User(
        username=username,
        password=hashed_password
    )

    db.session.add(new_user)

    db.session.commit()

    return jsonify({
        "message": "Registration successful"
    })


# =========================
# LOGIN WITH JWT
# =========================

@app.route('/login', methods=['POST'])

def login():

    data = request.json

    username = data['username']

    password = data['password']

    user = User.query.filter_by(
        username=username
    ).first()

    if user and check_password_hash(
        user.password,
        password
    ):

        token = jwt.encode({

            'user': username,

            'exp': datetime.datetime.utcnow()
                   + datetime.timedelta(hours=24)

        },

        app.secret_key,

        algorithm="HS256")

        return jsonify({

            "message": "Login successful",

            "token": token
        })

    return jsonify({
        "message": "Invalid credentials"
    })


# =========================
# SEND OTP
# =========================

@app.route('/send-otp', methods=['POST'])

def send_otp():

    data = request.json

    email = data['email']

    otp = str(random.randint(100000, 999999))

    otp_storage[email] = otp

    send_otp_email(email, otp)

    return jsonify({
        "message": "OTP sent successfully"
    })


# =========================
# VERIFY OTP
# =========================

@app.route('/verify-otp', methods=['POST'])

def verify_otp():

    data = request.json

    email = data['email']

    otp = data['otp']

    if otp_storage.get(email) == otp:

        return jsonify({
            "message": "OTP verified"
        })

    return jsonify({
        "message": "Invalid OTP"
    })


# =========================
# UPLOAD RESUME
# =========================

@app.route('/upload', methods=['POST'])

def upload_resume():

    global latest_result

    file = request.files['resume']

    filename = file.filename.lower()

    if filename.endswith('.pdf'):

        text = extract_text_from_pdf(file)

    elif filename.endswith('.docx'):

        text = extract_text_from_docx(file)

    else:

        return jsonify({
            "error": "Only PDF and DOCX supported"
        })

    result = analyze_resume(text)

    latest_result = result

    # SAVE TO DATABASE

    new_resume = Resume(

        score=result['score'],

        level=result['level'],

        skills=", ".join(
            result['skills_found']
        ),

        suggestions=", ".join(
            result['suggestions']
        )

    )

    db.session.add(new_resume)

    db.session.commit()

    return jsonify(result)


# =========================
# HISTORY
# =========================

@app.route('/history')

def history():

    resumes = Resume.query.all()

    data = []

    for r in resumes:

        data.append({

            "score": r.score,

            "level": r.level,

            "skills": r.skills,

            "suggestions": r.suggestions

        })

    return jsonify(data)


# =========================
# DOWNLOAD REPORT
# =========================

@app.route('/download-report')

def download_report():

    pdf_file = "resume_report.pdf"

    c = canvas.Canvas(pdf_file)

    c.setFont("Helvetica-Bold", 20)

    c.drawString(
        180,
        800,
        "CareerLens AI Report"
    )

    c.setFont("Helvetica", 14)

    c.drawString(
        50,
        740,
        f"Resume Score: {latest_result.get('score', 0)}"
    )

    c.drawString(
        50,
        710,
        f"Level: {latest_result.get('level', '')}"
    )

    c.drawString(
        50,
        670,
        "Skills Found:"
    )

    y = 640

    for skill in latest_result.get(
        'skills_found',
        []
    ):

        c.drawString(
            70,
            y,
            f"- {skill}"
        )

        y -= 25

    c.drawString(
        50,
        y - 20,
        "Suggestions:"
    )

    y -= 50

    for suggestion in latest_result.get(
        'suggestions',
        []
    ):

        c.drawString(
            70,
            y,
            f"- {suggestion}"
        )

        y -= 25

    c.save()

    return send_file(
        pdf_file,
        as_attachment=True
    )


# =========================
# RUN APP
# =========================

if __name__ == '__main__':

    app.run(debug=True)