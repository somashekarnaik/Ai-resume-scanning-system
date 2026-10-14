# Connecting the frontend and backend

## Run locally

Start the backend from the repository root:

```powershell
python -m uvicorn App.main:app --app-dir backend --reload --port 8000
```

In a second terminal, start the frontend:

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL printed in the frontend terminal (normally
`http://localhost:5173`). Vite proxies `/api/*` and `/health` to the backend at
`http://127.0.0.1:8000`.

The frontend uses relative API paths by default. For a separately hosted frontend,
set `VITE_API_URL` to the backend's base URL before building, for example:

```powershell
$env:VITE_API_URL = "https://api.example.com"
npm run build
```

For cross-origin deployment, set `BACKEND_CORS_ORIGINS` in the backend environment
to a comma-separated list of trusted frontend origins. Local Vite origins are
allowed by default. Keep secrets such as `OPENAI_API_KEY` on the backend only.
