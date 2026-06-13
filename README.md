# CareerLens AI 🚀

CareerLens AI is an AI-powered Placement Dashboard that helps students and job seekers analyze their resumes, improve their professional profiles, and prepare for interviews.

🌐 **Live Demo:** https://rococo-raindrop-a7e917.netlify.app

---

## 📌 Features

### Resume Analysis

* Upload PDF resumes
* Upload image-based resumes (PNG, JPG, JPEG)
* ATS-style Resume Scoring
* Career Match Analysis
* Placement Readiness Score
* Strengths & Weaknesses Detection
* Personalized Improvement Suggestions
* Skill Gap Analysis

### Interview Preparation

* HR Interview Questions
* Technical Interview Questions
* Project Viva Questions
* Mock Answer Evaluation
* Performance Feedback

### Career Development Tools

* AI-Generated Cover Letter
* LinkedIn Profile Optimizer
* Professional Headline Suggestions
* About Section Enhancement
* LinkedIn Improvement Checklist

### Report Management

* User Authentication
* Analysis History Tracking
* Downloadable PDF Reports
* Saved Resume Records

---

## 🛠️ Tech Stack

### Frontend

* HTML5
* CSS3
* JavaScript
* Chart.js
* Netlify Deployment

### Backend

* Python
* Flask
* Flask-CORS
* Flask-SQLAlchemy
* SQLite Database

### AI & Processing

* GROQ API
* PyPDF2
* pdfplumber
* python-docx
* pytesseract
* OpenCV
* Pillow

### Report Generation

* ReportLab

---

## 📂 Project Structure

```text
CareerLens-AI/
│
├── frontend/
│   ├── index.html
│   ├── auth.html
│   ├── style.css
│   └── script.js
│
├── backend/
│   ├── app.py
│   ├── database.db
│   ├── uploads/
│   └── requirements.txt
│
├── netlify.toml
├── README.md
└── LICENSE
```

---

## 🚀 Live Demo

Frontend:
https://rococo-raindrop-a7e917.netlify.app

---

## ⚙️ Backend Setup

### 1. Clone Repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd CareerLens-AI
```

### 2. Create Virtual Environment

```bash
cd backend
python -m venv venv
```

### 3. Activate Virtual Environment

Windows:

```bash
venv\Scripts\activate
```

Mac/Linux:

```bash
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure AI API (Optional)

```bash
set GROQ_API_KEY=YOUR_API_KEY
```

### 6. Run Server

```bash
python app.py
```

Backend runs on:

```text
http://127.0.0.1:5000
```

---

## 🔌 API Endpoints

### Health Check

```http
GET /health
```

### User Registration

```http
POST /register
```

### User Login

```http
POST /login
```

### Resume Upload

```http
POST /upload
```

### Analysis History

```http
GET /history?username=user
```

### Download Report

```http
GET /download-report
```

### Generate Cover Letter

```http
POST /generate-cover-letter
```

### LinkedIn Analysis

```http
POST /analyze-linkedin
```

### Mock Interview Evaluation

```http
POST /evaluate-mock-answer
```

---

## 📄 Sample Workflow

1. Register/Login
2. Upload Resume
3. Select Target Career Role
4. Get ATS Score
5. Review Skill Gap Analysis
6. Generate Cover Letter
7. Optimize LinkedIn Profile
8. Practice Interview Questions
9. Download PDF Report

---

## 💡 Key Benefits

* Improves Resume Quality
* Increases ATS Compatibility
* Helps Prepare for Interviews
* Identifies Missing Skills
* Creates Professional Cover Letters
* Enhances LinkedIn Profiles
* Tracks Career Progress

---

## 🔒 Notes

* OCR support available for image resumes.
* PDF reports generated automatically.
* Works with or without GROQ API.
* Local heuristic analysis available as fallback.

---

## 📈 Future Enhancements

* Multi-language Resume Analysis
* AI Resume Builder
* Job Recommendation Engine
* Real-time Interview Simulator
* Resume Ranking System
* Company-specific Interview Preparation

---

## 👩‍💻 Developer

**Diya Das**

B.Tech CSE Student | AI & Full Stack Developer

GitHub: DiyaDas222

LinkedIn: https://www.linkedin.com/in/diya-das-33b968302

---

## ⭐ Support

If you found this project useful, please give it a star on GitHub and share it with others.

⭐ Star this repository to support the project.
