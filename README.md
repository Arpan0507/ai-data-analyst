# 🧠 AI Data Analyst V3 — Multi-Agent System

A **production-grade, full-stack multi-agent AI data analyst** that automatically transforms raw CSV/Excel datasets into cleaned data, visualizations, insights, and a comprehensive report.

## ⚡ Architecture

```
React Frontend → FastAPI Backend → Multi-Agent Pipeline
                                    ├── Profiling Engine (pandas)
                                    ├── Planner Agent (LLM)
                                    ├── Validation Layer (rule-based)
                                    ├── Executor Agent (cleaning)
                                    ├── Visualization Engine (matplotlib/seaborn)
                                    ├── Statistical Engine (pandas)
                                    ├── Insight Agent (LLM)
                                    ├── Critic Agent (LLM validation)
                                    ├── Memory Layer (FAISS)
                                    └── Report Generator
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- An OpenRouter API key ([get one here](https://openrouter.ai/keys))

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env and add your OPENROUTER_API_KEY

# Start the server
python -m uvicorn main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

### 3. Open the App

Navigate to **http://localhost:5173** in your browser.

## 📊 Features

| Feature | Description |
|---------|-------------|
| **File Upload** | Drag-and-drop CSV/Excel upload with validation |
| **Data Profiling** | Automatic column stats, skewness, outlier detection |
| **AI Planning** | LLM generates cleaning + visualization plan |
| **Safety Validation** | Rule-based guardrails prevent unsafe operations |
| **Data Cleaning** | Automated fill, drop, convert, normalize, deduplicate |
| **Visualizations** | Histogram, bar, line, heatmap charts (dark themed) |
| **Statistical Summary** | Trends, growth rates, top categories |
| **AI Insights** | 3-5 specific, quantitative business insights |
| **Critic Agent** | Validates all outputs with quality scoring |
| **FAISS Memory** | Learns from past analyses for better future results |
| **NL Queries** | Ask questions about your data in plain English |
| **Report** | Complete report with all findings |

## 🏗️ Project Structure

```
V3/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── routes/
│   │   ├── upload.py         # Upload + pipeline orchestration
│   │   └── query.py          # NL query endpoint
│   ├── services/
│   │   ├── profiling.py      # Dataset profiling
│   │   ├── planner_agent.py  # Planner Agent
│   │   ├── validation.py     # Rule-based safety
│   │   ├── cleaning_engine.py# Pandas cleaning
│   │   ├── executor_agent.py # Executor Agent
│   │   ├── visualization_engine.py # Chart generation
│   │   ├── stats_engine.py   # Statistical summary
│   │   ├── insight_agent.py  # Insight Agent
│   │   ├── critic_agent.py   # Critic Agent
│   │   ├── memory.py         # FAISS memory
│   │   ├── nl_query.py       # NL query handler
│   │   └── report_generator.py # Report assembly
│   ├── schemas/models.py     # Pydantic models
│   └── utils/
│       ├── llm_client.py     # OpenRouter + JSON retry
│       └── helpers.py        # Utilities
├── frontend/
│   └── src/
│       ├── App.jsx           # Main app
│       └── components/       # React components
├── sample_data/
│   └── sales_sample.csv      # Test dataset
└── README.md
```

## 🔑 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENROUTER_API_KEY` | ✅ | — | Your OpenRouter API key |
| `LLM_MODEL` | ❌ | `openrouter/auto` | LLM model to use |
| `MAX_FILE_SIZE_MB` | ❌ | `50` | Max upload size in MB |

## 🧪 Testing with Sample Data

The `sample_data/sales_sample.csv` file contains a synthetic sales dataset with:
- 61 rows × 10 columns
- Missing values in Sales, Customer_Age, and Rating
- 1 duplicate row
- Date, categorical, and numeric columns

Upload it through the web interface to test the full pipeline.
