# CareerLens AI (Placement Dashboard)

CareerLens AI helps candidates upload a resume and receive ATS-style scoring, role-specific feedback, interview questions, and a tailored learning roadmap. It also supports generating a cover letter and auditing LinkedIn text.

> **Frontend:** static HTML (Netlify)
>
> **Backend:** Flask API (uploads, history, PDF report download, AI analysis)

---

## Features

- **Resume upload & analysis** (PDF + image files)
- **ATS score + career match score + placement readiness**
- **Strengths, weaknesses, and targeted suggestions**
- **Skill gap analysis**
- **Interview prep** (HR/technical/project viva questions + answer evaluation)
- **Advanced tools**
  - Generate a tailored **cover letter** (from your last analysis)
  - **LinkedIn profile optimizer** (headline + About + checklist)
- **History** (saved reports per username)
- **Download PDF report**

---

## Project Structure

- `frontend/` - static UI (`index.html`, `auth.html`)
- `backend/` - Flask app (`app.py`), database (`database.db`), uploads folder
- `netlify.toml` - Netlify redirects for direct route access

---

## Live Demo / Deployment

This project is configured for Netlify to publish the `frontend/` directory, and a separate Flask deployment (the UI expects a backend URL).

### Backend URL
- The UI uses `localStorage.backend_url` if configured.
- Otherwise it falls back to local dev (`http://127.0.0.1:5000`) and a production Render base URL.

In the UI: **Auth → ⚙️ Configure API Server**.

---

## Backend Setup (Flask)

### 1) Create a virtual environment

```bash
cd backend
python -m venv venv
venv\Scripts\activate
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) (Optional) Configure GROQ API key

The backend can run without an AI key by using a local heuristic fallback.

```bash
set GROQ_API_KEY=YOUR_KEY
```

### 4) Run the server

```bash
python app.py
```

Backend should be reachable at:

- `GET  /health`
- `POST /register`
- `POST /login`
- `POST /upload`
- `GET  /history?username=...`
- `GET  /download-report?report_id=...&username=...`
- `POST /generate-cover-letter`
- `POST /analyze-linkedin`
- `POST /evaluate-mock-answer`

---

## Frontend Setup

The frontend is static. If running locally:

1. Deploy or serve `frontend/index.html` and `frontend/auth.html`.
2. Configure the backend URL in the Auth screen (or run backend locally on port `5000`).

---

## API Quick Reference

### `POST /upload`

**FormData**:
- `resume` (file) - PDF or PNG/JPG/JPEG
- `target_career` (string) - role to tailor insights for
- `username` (string) - used for history storage

**Response:** JSON containing:
- `id`, `score`
- `local_analysis` (heuristic)
- `ai_feedback` (JSON string)

### `GET /download-report`

Query params:
- `report_id` (optional)
- `username` (optional, default `demo_user`)

Returns: a generated PDF report for the last (or specified) analysis.

---

## Notes / Requirements

- **OCR for images** uses `pytesseract`. If you upload images and OCR can’t run (missing system dependency), the backend will return a clear error suggesting to upload a clearer/text-based PDF.
- **AI mode:** set `GROQ_API_KEY` to enable full AI analysis. Without it, the app still works using a local heuristic.

---

## License

No license file is included in this repository. Add one if you plan to publish publicly.

