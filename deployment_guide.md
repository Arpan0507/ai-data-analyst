# Deployment Guide - AI Data Analyst

This guide explains how to deploy the AI Data Analyst system to a production environment.

## 1. Prerequisites
- An **OpenRouter API Key** (or OpenAI/Anthropic keys if you modify the client).
- A cloud provider account (e.g., [Render](https://render.com), [Railway](https://railway.app), or [Fly.io](https://fly.io)).

## 2. Environment Variables
You must set the following variables in your production environment:

| Variable | Description |
| :--- | :--- |
| `OPENROUTER_API_KEY` | Your API key for LLM access. |
| `LLM_MODEL` | (Optional) The model to use (default: `openrouter/auto`). |
| `MAX_FILE_SIZE_MB` | Max upload size (e.g., `50`). |
| `PORT` | The port the backend will run on (usually provided by the host). |

## 3. Recommended Deployment Strategies

### Option A: The "Unified" Docker Strategy (Easiest)
This bundles the frontend and backend into a single container.
1. Build the Docker image: `docker build -t ai-data-analyst .`
2. Run it: `docker run -p 8000:8000 -e OPENROUTER_API_KEY=your_key ai-data-analyst`

### Option B: Managed Services (Render/Railway)
1. **Backend**: 
   - Connect your GitHub repo.
   - Set Build Command: `pip install -r requirements.txt`
   - Set Start Command: `python -m uvicorn main:app --host 0.0.0.0 --port $PORT`
2. **Frontend**:
   - Set Build Command: `npm install && npm run build`
   - Set Publish Directory: `dist`
   - (Note: You'll need to update `Vite` proxy or use absolute URLs for the API).

## 4. Persistent Storage (Crucial)
The app stores **Charts**, **Uploads**, and **FAISS Memory** in the `backend/data` folder.
- On most cloud platforms (like Render), the disk is **ephemeral** (files disappear after restart).
- **Fix**: Mount a **Persistent Volume** to the `/app/backend/data` directory in your cloud dashboard.

## 5. Security Checklist
- [ ] Disable `CORSMiddleware` for localhost and only allow your production domain.
- [ ] Use a production-grade WSGI server like `gunicorn` with `uvicorn` workers.
- [ ] Ensure `DEBUG` modes are off.
