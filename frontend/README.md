# Smart Resume Screener — Frontend


This is a Vite + React frontend that connects to the FastAPI backend in `../backend`.

Pre-requisites:
- Node.js and npm installed (recommended: Node 18+)
- Backend running at http://localhost:8000 (default)

Quick start (PowerShell):

```powershell
cd c:\intelFPGA\18.1\3d\rs\frontend
npm install --legacy-peer-deps
npm run dev
```

Environment overrides:
- To point the frontend to a backend running elsewhere set `VITE_API_BASE` env var before starting Vite. Example (PowerShell):

```powershell
$env:VITE_API_BASE='http://127.0.0.1:8000'; npm run dev
```

GEMINI API key (backend):
- The backend expects the Gemini API key in the environment variable `GEMINI_API_KEY`, or inside a `.env` file in the `backend/` folder. Example `.env` file:

	GEMINI_API_KEY=your_api_key_here

Start the backend (PowerShell):

```powershell
cd c:\intelFPGA\18.1\3d\rs\backend
python -m pip install -r requirements.txt
python main.py
```

If you want, I can add a short-lived backend endpoint to set the key at runtime for local testing — tell me if you'd like that.

