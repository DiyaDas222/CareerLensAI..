Netlify Auto-Deploy Setup
=========================

This project includes a GitHub Actions workflow that can automatically deploy the `frontend/` folder to Netlify when `main` is updated.

What to add in GitHub Secrets
- `NETLIFY_AUTH_TOKEN` — a personal access token from Netlify (User Settings → Applications → Personal access tokens).
- `NETLIFY_SITE_ID` — your Netlify site ID (Site settings → Site information → Site ID).

How it works
- On push to `main` (changes under `frontend/`), the workflow zips the `frontend` directory and POSTs the zip to Netlify's Deploys API.

How to trigger a deploy now
- Push a commit to `main` or trigger a redeploy from the Netlify dashboard.

Notes
- If you prefer using the official Netlify CLI or a community GitHub Action, you can replace the curl step with the action of your choice.
