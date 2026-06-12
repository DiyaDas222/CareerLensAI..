# TODO - CareerLensAI fix sweep

## Backend
- [x] Fix missing `target_career` argument in AI feedback generation.
- [x] Repair/replace broken `backend/app.py` so `/upload` works and returns `ai_feedback`.
- [x] Make `/upload` accept PNG/JPG (OCR) and return clear JSON errors for unsupported types.

## Frontend
- [x] Use relative URLs in `frontend/index.html` for `/upload` and `/download-report`.
- [x] Fix `frontend/auth.html` to use relative `/register` and `/login`.
- [x] Improve error handling: show backend `error` message instead of generic alert.


## Next recommended
- [ ] Make `/download-report` reflect the last analyzed resume (currently static).

