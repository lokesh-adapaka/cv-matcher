# AI CV Matcher & Generator

Upload your CV (PDF), and AI will analyze your skills, find matching jobs from Adzuna, show match percentages, and generate a tailored CV optimized for any job.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React + Vite + Tailwind CSS |
| Backend | Python FastAPI |
| AI | Azure OpenAI (GPT-4o-mini) |
| Database | Azure CosmosDB |
| Job API | Adzuna |

## Features

- **CV Upload & Parsing** — Upload a PDF CV; AI extracts name, skills, experience, education
- **Job Matching** — Fetches jobs from Adzuna, AI computes match percentage per job
- **Skill Gap Analysis** — Shows matched skills and missing skills per job
- **Tailored CV Generation** — AI rewrites your CV for a specific job, downloads as PDF
- **Match Filtering** — Filter by minimum match score, sort by percentage or company

## Prerequisites

- Python 3.11+
- Node.js 18+
- Azure OpenAI resource (with a GPT-4o-mini or GPT-4o deployment)
- Azure CosmosDB account
- Adzuna API credentials (free at https://developer.adzuna.com/)

## Setup

### 1. Clone & configure environment

```bash
cd cv-matcher/backend
cp .env.example .env
# Edit .env with your Azure OpenAI, CosmosDB, and Adzuna credentials
```

### 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at http://localhost:5173 and proxies API calls to http://localhost:8000.

### 4. Docker (alternative)

```bash
docker compose up --build
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/cv/upload` | Upload and parse a PDF CV |
| GET | `/api/cv/{cv_id}` | Retrieve parsed CV data |
| GET | `/api/jobs/search?skills=...` | Search jobs by skills |
| POST | `/api/match` | Match CV against jobs |
| GET | `/api/match/{cv_id}` | Get stored match results |
| POST | `/api/cv/generate` | Generate tailored CV PDF |
| GET | `/api/health` | Health check |

## Project Structure

```
cv-matcher/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry
│   │   ├── config.py            # Environment configuration
│   │   ├── routers/
│   │   │   ├── cv.py            # CV upload & generation endpoints
│   │   │   ├── jobs.py          # Job search endpoint
│   │   │   └── match.py         # Matching endpoint
│   │   ├── services/
│   │   │   ├── ai_service.py    # Azure OpenAI integration
│   │   │   ├── cv_parser.py     # PDF text extraction
│   │   │   ├── cv_generator.py  # PDF CV generation (reportlab)
│   │   │   ├── job_service.py   # Adzuna API client
│   │   │   └── matcher.py       # Matching orchestrator
│   │   ├── models/
│   │   │   ├── cv.py            # CV data models
│   │   │   └── job.py           # Job & match models
│   │   └── db/
│   │       └── cosmos.py        # CosmosDB client
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Router & layout
│   │   ├── main.jsx             # Entry point
│   │   ├── pages/
│   │   │   ├── UploadPage.jsx   # CV upload & parsing UI
│   │   │   └── MatchResultsPage.jsx # Match results & filters
│   │   ├── components/
│   │   │   ├── CVUploader.jsx   # Drag-and-drop uploader
│   │   │   ├── JobCard.jsx      # Job match card
│   │   │   ├── MatchScore.jsx   # Circular score indicator
│   │   │   └── SkillTag.jsx     # Colored skill badge
│   │   └── services/
│   │       └── api.js           # API client (axios)
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
└── docker-compose.yml
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI resource endpoint |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key |
| `AZURE_OPENAI_DEPLOYMENT` | Model deployment name (default: gpt-4o-mini) |
| `AZURE_OPENAI_API_VERSION` | API version (default: 2024-12-01-preview) |
| `COSMOS_ENDPOINT` | CosmosDB account endpoint |
| `COSMOS_KEY` | CosmosDB primary key |
| `COSMOS_DATABASE` | Database name (default: cvmatcher) |
| `ADZUNA_APP_ID` | Adzuna application ID |
| `ADZUNA_APP_KEY` | Adzuna application key |
