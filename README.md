# Automated Land Dispute Monitoring System (LandWatch)

An end-to-end, AI-powered system designed to scrape regional newspapers, run OCR and entity extraction on public legal notices, classify land disputes with LLMs, cluster related litigations, and deliver real-time notifications to real estate clients through an interactive web dashboard, REST APIs, and signed webhooks.

---

## Key Features

1. **OCR Extraction Pipeline**:
   - OpenCV image preprocessing (deskewing, adaptive Gaussian thresholding, noise reduction).
   - PyTesseract word confidence parsing & `pdf2image` multi-page conversion.
   - Regex-based property/survey number, disputing parties, court/authority, and location extraction.

2. **AI-Driven Dispute Analysis & Classification**:
   - Multi-provider LLM integration (OpenAI GPT-4o / Anthropic Claude).
   - Structured JSON analysis: dispute severity, urgency score (1-10), and real estate impact assessment.
   - Cross-notice dispute clustering based on survey number and party overlap.

3. **Interactive Web Dashboard**:
   - **Overview**: Real-time KPI summary cards, interactive Chart.js visualizations (Severity distribution, timeline trends, top regions, status).
   - **Disputes**: Filterable, paginated table with urgency meters, severity badges, and drill-down detail views with OCR source text.
   - **Sources**: Newspaper source management with scraping frequencies and custom CSS selectors.
   - **Subscriptions**: Region & survey property tracking preferences for clients.
   - **Alert Inbox**: Real-time notification inbox with AJAX read/unread toggles.

4. **Background Task Processing**:
   - Celery Beat scheduled tasks for scraping, OCR queue processing, AI classification, dispute clustering, and webhook/email alert dispatch.

---

## Quick Start & Running Locally

### 1. Prerequisites
- Python 3.10+
- Tesseract OCR (optional for full OCR runs)

### 2. Setup Virtual Environment
```bash
cd land-dispute-monitor
python -m venv venv
venv\Scripts\activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Initialize Database & Seed Demo Data
```bash
python manage.py init-db
python manage.py seed-demo
```
> **Default Admin Login**:
> - **Email**: `admin@landwatch.com`
> - **Password**: `admin123`

### 4. Start Web Application
```bash
python wsgi.py
# or using Flask CLI:
flask --app manage.py run --port 5000 --debug
```
Open your browser at `http://localhost:5000`.

### 5. Running Celery Worker & Beat (Optional)
```bash
# Start Celery worker:
celery -A app.extensions.celery worker --loglevel=info

# Start Celery beat scheduler:
celery -A app.extensions.celery beat --loglevel=info --config=celeryconfig
```

---

## Running with Docker Compose

Deploy the entire stack (Web App, Celery Worker, Celery Beat, PostgreSQL, and Redis) in one command:

```bash
docker-compose up -d --build
```

Access the web dashboard at `http://localhost:5000`.

---

## Running Automated Tests

```bash
python -m pytest tests/ -v
```

All 41 unit and integration tests covering OCR preprocessing, entity extraction, AI analysis, API authorization, deduplication, and scraper logic.

---

## API Reference (`/api/v1`)

All REST endpoints require the `X-API-Key` header:

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/disputes` | `GET` | List disputes with filtering (`location`, `severity`, `status`, `type`, `date_from`, `date_to`) |
| `/api/v1/disputes/<id>` | `GET` | Retrieve dispute details with associated extracted notices |
| `/api/v1/disputes/clusters/<id>` | `GET` | Get all linked disputes within a cluster |
| `/api/v1/subscribe` | `POST` | Create tracking subscription |
| `/api/v1/subscriptions/<id>` | `GET`, `PUT`, `DELETE` | Manage subscription |
| `/api/v1/sources` | `GET`, `POST` | List and register newspaper sources |
| `/api/v1/sources/<id>` | `PUT`, `DELETE` | Update and deactivate sources |
| `/api/v1/clients/<id>/alerts` | `GET` | Fetch alerts for client |
| `/api/v1/alerts/<id>/read` | `PUT` | Mark alert as read |
