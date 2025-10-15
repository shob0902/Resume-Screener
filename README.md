![Loader animation](/frontend/public/loader.png)
# Resume Screener

A small demo app that parses candidate resumes (PDF), extracts skills and other structured fields, and matches candidates to a job description using an LLM-backed scoring engine.

This repository contains a React frontend (Vite) and a Python backend (FastAPI). The frontend provides a simple UI to upload multiple PDFs and a job description; the backend performs parsing, embedding/LLM scoring, and returns match scores and extracted metadata.

## Project structure

- `frontend/` - React app (Vite)
  - `src/` - React source files
  - `public/` - static assets
  - `index.html`, `package.json`, `vite.config.js`
- `backend/` - Python FastAPI backend
  - `main.py` - app entry
  - other modules: `database.py`, `resume_parser.py`, `llm_matcher.py`, etc.

## Requirements

- Node.js (16+ recommended)
- Python 3.10+
- pip or virtualenv for Python dependencies

## Frontend - setup & run

1. Install dependencies

```bash
cd frontend
npm install
```

2. Run the dev server

```bash
npm run dev
```

3. Build for production

```bash
npm run build
```

## Backend - setup & run

Create and activate a virtual environment, then install requirements:

```bash
cd backend
python -m venv .venv
# On Windows PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run the FastAPI server (development):

```bash
uvicorn main:app --reload --port 8000
```

The API endpoints used by the frontend include `/batch-upload` and `/match` (see `backend/main.py`).

## Configuration

- Place static images (e.g., `loader.png`) in `frontend/public/` so they are available at `/loader.png`.
- If using external Lottie animations, ensure the URLs used in the frontend are valid.

## Notes & development tips

- The frontend uses a client-side injected `dotlottie-wc` webcomponent for animations to keep the bundle small.
- Results from a screening run are stored in `localStorage` under the key `screen_results` before navigating to `/results`.
- The `Results` page includes a radar chart (Chart.js via `react-chartjs-2`) and a candidate report layout.
- Deduplication is performed client-side in `Results.jsx` (normalized by email/name/filename, highest overall_score kept).

## Contributing

Pull requests are welcome. For larger changes, please open an issue first to discuss the proposed changes.

## License

This project is intended for internal/demo use. Add a license file if you plan to open-source it.
