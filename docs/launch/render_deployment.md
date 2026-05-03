# SafeBite Render Deployment

## Render dashboard settings

- New resource: Web Service
- Repository: SafeBite GitHub repo
- Root Directory: backend
- Runtime: Python 3
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn mainBE:app --host 0.0.0.0 --port $PORT`
- Plan: Free for now

## Python version

The backend includes `backend/.python-version` with `3.9.18` so Render builds with the same Python major/minor version expected by the app.

## Startup data bootstrap

The backend uses SQLite at `backend/safebite.db`. On Render Free, the service filesystem is temporary, so a deploy, restart, or instance replacement can leave the SQLite database missing or empty.

On startup, `mainBE.py` initializes SQLite and checks the product count. If the `products` table is empty, it runs the existing import pipeline from `run_imports.py`, then checks JSON seed products and sample offers. The startup log prints the final product count and whether barcode `5000177025658` is present.

This is a temporary production bridge. The next durable production fix is Postgres, but that migration should happen separately after the current product endpoint is working on Render.

## URLs to test after deploy

- `https://safebite-backend-ivy7.onrender.com/`
- `https://safebite-backend-ivy7.onrender.com/health`
- `https://safebite-backend-ivy7.onrender.com/products/barcode/5000177025658`

## Expected endpoint behavior

- `/` returns `{"message":"SafeBite backend is running"}`
- `/health` returns HTTP 200
- `/products/barcode/5000177025658` returns the seeded Cow & Gate product instead of 404
