# SokoSure

SokoSure is a FastAPI backend for micro-insurance workflows, designed around user onboarding, policy recommendations, payments, and claims handling.

## Features

- User registration and login with PIN hashing
- Policy recommendation and policy management modules (scaffolded)
- Premium payment initiation and callback handling
- Claim submission, tracking, and status updates
- Notification and USSD modules (scaffolded)
- Async database access with SQLAlchemy/SQLModel
- Alembic migrations for schema versioning

## Tech Stack

- Python 3.11+
- FastAPI
- SQLModel + SQLAlchemy (async)
- PostgreSQL (`asyncpg`)
- Alembic
- Uvicorn
- Pydantic v2

## Project Structure

```text
app/
  core/
    config.py
    database.py
  features/
    users/
    recommendations/
    policies/
    payments/
    claims/
    notifications/
    ussd/
  main.py
alembic/
alembic.ini
requirements.txt
```

## Prerequisites

- Python installed
- PostgreSQL database
- `pip` available

## Setup

1. Clone the repository:

```bash
git clone https://github.com/SoonAnthony/SokoSure.git
cd SokoSure
```

2. Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows (PowerShell):

```powershell
.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source .venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql+asyncpg://<user>:<password>@<host>:<port>/<database>
```

5. Run migrations:

```bash
alembic upgrade head
```

6. Start the API server:

```bash
uvicorn app.main:app --reload
```

## API Docs

When the server is running:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Current API Endpoints

### Users (`/users`)

- `POST /users/register` - Register a user
- `POST /users/login` - Login user
- `GET /users/{user_id}` - Get user profile
- `PATCH /users/pin` - Update user PIN

### Payments (`/payments`)

- `POST /payments/initiate` - Initiate premium payment
- `POST /payments/callback` - Handle payment callback
- `GET /payments/{payment_id}` - Get payment details

### Claims (`/claims`)

- `POST /claims` - Submit a claim
- `GET /claims/{claim_id}` - Get claim by ID
- `GET /claims/user/{user_id}` - Get user claim history
- `PATCH /claims/{claim_id}` - Update claim status

## Modules Registered (Scaffolded/To Be Expanded)

These routers are wired in `app/main.py` and can be expanded with additional endpoints:

- `/ussd`
- `/recommendations`
- `/policies`
- `/notifications`

## Development Notes

- Database session dependency is provided via `app.core.database.get_session`.
- App settings are loaded from environment variables in `app.core.config.Settings`.
- Existing migrations are located in `alembic/versions/`.

## License

This project includes a `LICENSE` file at the repository root.

SokoSure is a FastAPI backend for micro-insurance workflows, designed around onboarding, policy recommendations, premium payments, and claims processing.

## Features

- User registration, login, PIN update, and profile retrieval
- Premium payment initiation and callback handling
- Automatic policy activation after confirmed payment
- Claim submission, status updates, and user claim history
- SQLModel + Alembic database setup for schema management

## Tech Stack

- Python
- FastAPI
- SQLModel / SQLAlchemy (async)
- PostgreSQL (via `asyncpg`)
- Alembic (migrations)
- Pydantic v2

## Project Structure

```text
app/
  core/
    config.py
    database.py
  features/
    users/
    ussd/
    recommendations/
    policies/
    payments/
    claims/
    notifications/
  main.py
alembic/
requirements.txt
```

## API Overview

Base app title: `SokoSure`

### Implemented Endpoints

#### Users (`/users`)
- `POST /users/register`
- `POST /users/login`
- `GET /users/{user_id}`
- `PATCH /users/pin`

#### Payments (`/payments`)
- `POST /payments/initiate`
- `POST /payments/callback`
- `GET /payments/{payment_id}`

#### Claims (`/claims`)
- `POST /claims`
- `GET /claims/{claim_id}`
- `GET /claims/user/{user_id}`
- `PATCH /claims/{claim_id}`

### Router Prefixes Registered in App

The following routers are mounted in `app/main.py`:

- `/users`
- `/ussd`
- `/recommendations`
- `/policies`
- `/payments`
- `/claims`
- `/notifications`

## Getting Started

### 1) Clone the repository

```bash
git clone https://github.com/SoonAnthony/SokoSure.git
cd SokoSure
```

### 2) Create and activate a virtual environment

On Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

On Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3) Install dependencies

```bash
pip install -r requirements.txt
```

### 4) Configure environment variables

Create a `.env` file at the project root:

```env
DATABASE_URL=postgresql+asyncpg://<user>:<password>@<host>:<port>/<database>
```

### 5) Run database migrations

```bash
alembic upgrade head
```

### 6) Start the API server

```bash
uvicorn app.main:app --reload
```

## API Docs

Once running locally:

- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## Development Notes

- Async database sessions are provided via `app/core/database.py`
- Settings are loaded from `.env` through `pydantic-settings`
- Feature modules are organized by domain (`users`, `payments`, `claims`, etc.)

## License

This project is licensed under the terms in the `LICENSE` file.