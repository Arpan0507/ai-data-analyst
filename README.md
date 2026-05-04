# 🧠 AI Data Analyst — Multi-Agent System

A **production-grade, full-stack multi-agent AI data analyst** that automatically transforms raw CSV/Excel datasets into cleaned data, visualizations, insights, and a comprehensive report.

## ⚡ Architecture

```
React Frontend (Vercel) → FastAPI Backend (Render) → Multi-Agent Pipeline
                                                     ├── Profiling Engine (pandas)
                                                     ├── Planner Agent (LLM)
                                                     ├── Validation Layer (rule-based)
                                                     ├── Executor Agent (cleaning)
                                                     ├── Visualization Engine (matplotlib/seaborn)
                                                     ├── Statistical Engine (pandas)
                                                     ├── Insight Agent (LLM)
                                                     ├── Critic Agent (LLM validation)
                                                     ├── Memory Layer (Hash-based/FAISS)
                                                     └── Report Generator
```

## 🚀 Deployment (Production)

This project is optimized for a split deployment: **Backend on Render** and **Frontend on Vercel**.

### 1. Backend (Render)
- **Runtime**: Python 3
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python -m uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Environment Variables**:
    - `OPENROUTER_API_KEY`: (Set this in Render Dashboard)
    - `FRONTEND_URL`: https://ai-data-analyst-rouge.vercel.app
- **One-Click Setup**: Use the included `render.yaml` file for automatic configuration.

### 2. Frontend (Vercel)
- **Framework**: Vite
- **Root Directory**: `frontend`
- **Environment Variables**:
    - `VITE_API_BASE_URL`: https://ai-data-analyst-7kic.onrender.com

---

## 🛠️ Local Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- An OpenRouter API key

### 1. Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
# Create .env and add OPENROUTER_API_KEY
python -m uvicorn main:app --reload --port 8000
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## 📊 Features

| Feature | Description |
|---------|-------------|
| **File Upload** | Drag-and-drop CSV/Excel upload with validation |
| **Data Profiling** | Automatic column stats, skewness, outlier detection |
| **AI Planning** | LLM generates cleaning + visualization plan |
| **Safety Validation** | Rule-based guardrails prevent unsafe operations |
| **Data Cleaning** | Automated fill, drop, convert, normalize, deduplicate |
| **Visualizations** | Histogram, bar, line, heatmap charts (Base64 encoded) |
| **AI Insights** | Specific, quantitative business insights |
| **Critic Agent** | Validates all outputs with quality scoring and retries |
| **Free Tier Ready** | Optimized for Render/Vercel free tiers (no persistent disk needed) |
| **Report** | Complete dashboard with all findings and CSV download |

---

## 🏗️ Project Structure

```
AiDataAnalyst/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── routes/
│   │   └── upload.py        # Upload + pipeline orchestration
│   ├── services/
│   │   ├── profiling.py      # Dataset profiling
│   │   ├── planner_agent.py  # Planner Agent
│   │   ├── visualization_engine.py # Chart generation (Base64)
│   │   ├── insight_agent.py  # Insight Agent
│   │   ├── critic_agent.py   # Critic Agent
│   │   └── report_generator.py # Report assembly
│   ├── schemas/models.py     # Pydantic models
├── frontend/
│   ├── src/
│   │   ├── api.js            # API client with dynamic base URL
│   │   ├── App.jsx           # Main dashboard
│   │   └── components/       # React components
├── render.yaml               # One-click Render deployment config
└── .dockerignore             # Optimized build context
```

## 🔑 Environment Variables

| Variable | Location | Required | Description |
|----------|----------|----------|-------------|
| `OPENROUTER_API_KEY` | Backend | ✅ | Your OpenRouter API key |
| `FRONTEND_URL` | Backend | ✅ | Allowed Vercel origin for CORS |
| `VITE_API_BASE_URL` | Frontend | ✅ | Render backend URL for API calls |
| `MAX_FILE_SIZE_MB` | Backend | ❌ | Max upload size (Default: 50) |

## 💡 Free Tier Optimizations
- **No Disk Required**: Charts are generated as Base64 strings and sent in the JSON response.
- **Memory Efficient**: Heavy models (sentence-transformers) are optional to fit within 512MB RAM.
- **Streaming Downloads**: Cleaned CSVs are generated on-the-fly from memory.
