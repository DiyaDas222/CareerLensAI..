# Reddit Post Showcase: CareerLens AI 🚀

Here is a ready-to-use markdown template for you to share CareerLens AI on Reddit (ideal for subreddits like **r/SideProject**, **r/webdev**, **r/Python**, or **r/selfhosted**).

***

**Suggested Titles:**
1. *[Show r/SideProject] CareerLens AI - Open-source placement preparation hub & resume auditor with voice-activated mock interviews*
2. *I built an AI Career Coach that does resume rewrites, custom learning planners, cover letter generation, and real-time voice interviews*
3. *Show r/webdev: CareerLens AI – Bridge the gap to your dream career with interactive resume audits and study plans*

***

### Post Body:

Hey r/SideProject,

I wanted to share a project I've been working on called **CareerLens AI**. 

As a student, it can be extremely difficult to know how closely your resume aligns with what companies actually want for your target role, what skills you are missing, and how to practice for interviews.

I built CareerLens AI to act as a comprehensive, all-in-one AI career counselor, placement advisor, and mock interview assistant.

Here is a quick look at what it does:

### 🌟 Key Features:
1. **Multi-Metric Scoring**: Instantly evaluates your profile to yield three scores: an **ATS Resume Formatting Rating**, a **Career Match Score** tailored to your dream job, and a **Placement Readiness Level**.
2. **Deep Resume Auditing**: Breaks down resume strengths, structural weaknesses, and gives general format suggestions.
3. **Skill Gap Mapping**: Displays a visual layout comparing detected skills against missing competencies required for your dream career.
4. **Action-Oriented Resume Rewrites**: Provides side-by-side phrasing improvements to turn weak resume bullet points into high-impact, metrics-driven descriptions.
5. **Voice-Enabled Mock Interview Simulator**: Selects HR, Technical, or project-specific questions and uses the browser's Web Speech API to speak the questions aloud (TTS) and record your spoken answers (STT) for instant AI scoring and critique.
6. **Timeline Roadmap & Weekly Study Planner**: Compiles a phase-by-step career milestones roadmap and a Monday-to-Sunday learning schedule based on your gaps.
7. **Advanced Utilities**: Built-in generators for custom cover letters, a LinkedIn profile auditor, and curated study resource recommendations.
8. **Dynamic PDF Reports**: Compiles all of your metrics, gap charts, and planner schedules into a professionally formatted multi-page PDF using ReportLab.
9. **History Tracker**: Keeps a log of past resume runs to reload dashboard details instantly.

---

### 🛠️ The Tech Stack:
* **Frontend**: HTML5, Vanilla CSS (with glassmorphism/dark theme), JavaScript (ES6), Chart.js (donut gauge widgets), and Web Speech API.
* **Backend**: Python 3.13, Flask, SQLAlchemy (SQLite), pdfplumber (resume parsing), and ReportLab (PDF compilation).
* **AI Engine**: Groq API powered by `llama-3.3-70b-versatile` running in JSON mode for structured outputs.
* **Hosting**: Netlify (Frontend) & Render (Backend).

---

### 💻 Open Source / Repository:
The code is committed and pushed directly to GitHub. 

I’d love to hear your thoughts on:
* What other features you'd find useful (e.g., job application tracking, multi-resume comparison)?
* UX/UI feedback on the glassmorphic dark theme dashboard.
* What subreddits or communities I should share this with next.

Let me know what you think!
