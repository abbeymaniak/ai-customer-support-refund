# AI-Powered Customer Support Refund System

An automated, intelligent e-commerce customer support refund decision engine built with **FastAPI**, **React 18 / Vite / TypeScript**, **PostgreSQL 16**, and **LiteLLM**.

The system evaluates incoming refund requests against a structured, machine-readable store policy, customer purchase history, and fraud risk metrics, producing defensible decisions: **Approved**, **Denied**, or **Escalated**.

---

## Architecture Overview

```
                      +-----------------------------+
                      |   React 18 SPA (Vite)       |
                      |   Tailwind CSS / Nginx      |
                      |   (Port 3000)               |
                      +--------------+--------------+
                                     |
                                     | HTTP / REST
                                     v
                      +-----------------------------+
                      |   FastAPI Backend           |
                      |   Uvicorn (Port 8000)       |
                      +-------+--------------+------+
                              |              |
          SQLAlchemy (async)  |              | LiteLLM
                              v              v
               +--------------------+   +-----------------------+
               |  PostgreSQL 16     |   | Multi-Provider AI     |
               |  (Port 5432)       |   | (OpenAI / Ollama /    |
               |  JSONB Audit Logs  |   |  Anthropic / Gemini)  |
               +--------------------+   +-----------------------+
```

### Core Stack
- **Backend:** FastAPI (Python 3.11), SQLAlchemy 2.0 (asyncio + asyncpg), Alembic, Pydantic v2, structlog.
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS v4, TanStack Query, React Router v6, Axios, Lucide Icons.
- **AI Integration:** LiteLLM (unified multi-provider SDK with automatic fallback support).
- **Database:** PostgreSQL 16 with JSONB support for audit trails and policy checks.
- **Orchestration:** Docker & Docker Compose (single command multi-container setup).

---

## Quickstart with Docker Compose

1. **Clone and Navigate:**
   ```bash
   git clone https://github.com/abbeymaniak/ai-customer-support-refund.git
   cd ai-customer-support-refund
   ```

2. **Configure Environment:**
   Copy the example environment configuration:
   ```bash
   cp .env.example .env
   ```
   Add your LLM API key (e.g. `OPENAI_API_KEY`) or configure Ollama for local execution.

3. **Start All Services:**
   ```bash
   docker compose up --build
   ```

4. **Verify Application Services:**
   - **Frontend UI:** [http://localhost:3000](http://localhost:3000)
   - **Interactive Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
   - **Backend Health Check:** [http://localhost:8000/health](http://localhost:8000/health)
   - **PostgreSQL Database:** `localhost:5432` (`refunds_user` / `refunds_pass`)

---

## Database Seeding & Mock Personas

On first initialization, PostgreSQL automatically executes `data/seed.sql` mounting to `/docker-entrypoint-initdb.d/01_seed.sql`. This populates 16 diverse customer personas covering various edge cases:

- **Low-Risk Loyal Spender:** `sarah.jenkins@example.com` ($3,200+ spent, 18 orders, 0 refunds)
- **High-Risk Serial Returner:** `marcus.vance@example.com` (60% return rate, 3 refunds, flagged)
- **VIP Customer:** `victoria.sterling@example.com` ($12,400+ spent, 32 orders)
- **Non-Refundable Item Buyer:** `amanda.price@example.com` (clearance item return request)
- **High-Value Item Buyer:** `james.wilson@example.com` ($650 item exceeding $500 auto-threshold)
- **Expired Window Buyer:** `kevin.chen@example.com` (order delivered 40 days ago, exceeding 30-day window)

---

## Machine-Readable Policy (`data/refund_policy.json`)

The policy engine enforces structured rules:
- **Return Window:** 30 days from delivery (exception for damaged/defective items).
- **Auto-Approval Threshold:** Max $100 for normal orders.
- **Escalation Threshold:** Any single item claim > $500 requires human review.
- **Customer Risk Threshold:** Return rate >= 40% or >= 3 previous refunds triggers escalation.
- **Non-Refundable Categories:** Gift cards, perishables, digital downloads, clearance items.

---

## Local Development (Without Docker)

### Backend:
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend:
```bash
cd frontend
npm install
npm run dev
```
Accessible at [http://localhost:5173](http://localhost:5173).

---

## Testing

### Backend Tests

#### Option 1: Run via Docker Compose (Recommended)
When Docker is running, execute tests directly inside the backend container without needing local Python setup:

```bash
docker compose exec backend pytest
```

To run a specific test file:

```bash
docker compose exec backend pytest tests/test_security_validation.py
```

#### Option 2: Run Locally on Host
If running directly on your machine outside Docker, activate the virtual environment first so required dependencies such as `httpx` are loaded:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

> **Note**: Running `pytest` directly on your host without activating `.venv` uses your global Python environment, which will trigger `ModuleNotFoundError: No module named 'httpx'`. Always activate the virtual environment or run via Docker.

### Frontend Tests

Run the Vitest unit testing suite:

```bash
cd frontend
npm test
```

Build the production bundle and verify TypeScript types:

```bash
cd frontend
npm run build
```
