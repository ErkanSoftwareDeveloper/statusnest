# StatusNest

StatusNest is a backend uptime monitoring service built with FastAPI, MySQL, Redis, Celery, and Docker.

It allows users to create website monitors, automatically check their availability, store historical results, detect outages, and track incidents.

**Current version:** `v0.1.0` — Backend MVP

## Features

- User registration and login
- JWT authentication
- User-specific monitor management
- Create, update, list, and delete monitors
- Manual website checks
- Automatic scheduled checks with Celery Beat
- Background processing with Celery workers
- Redis message broker
- MySQL persistence
- Check history
- Monitor statistics
- Automatic incident detection
- Automatic incident recovery
- Incident history
- Authorization between users
- SSRF protection for monitored URLs
- Environment-based secret management
- Automated tests with pytest

## Tech Stack

- Python
- FastAPI
- SQLAlchemy
- MySQL 8
- Alembic
- Redis
- Celery
- Celery Beat
- HTTPX
- JWT / PyJWT
- Docker
- Docker Compose
- Pytest

## Architecture

```text
                    ┌──────────────┐
                    │   FastAPI    │
                    │     API      │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │    MySQL     │
                    └──────────────┘

                           ▲
                           │
                    ┌──────┴───────┐
                    │ Celery Worker│
                    └──────▲───────┘
                           │
                    ┌──────┴───────┐
                    │    Redis     │
                    └──────▲───────┘
                           │
                    ┌──────┴───────┐
                    │ Celery Beat  │
                    └──────────────┘
```

Celery Beat periodically schedules active monitors.

Celery workers perform website checks and save the results to MySQL. If a website becomes unavailable, StatusNest opens an incident. When the website becomes available again, the incident is automatically resolved.

## Monitor Lifecycle

```text
Website UP
    │
    ▼
Check result stored
    │
    ▼
Website DOWN
    │
    ▼
Incident opened
    │
    ▼
Website still DOWN
    │
    ▼
Existing incident remains open
    │
    ▼
Website UP again
    │
    ▼
Incident resolved
```

## Security

StatusNest includes several backend security protections.

### Authentication

Protected endpoints require a JWT access token.

JWT secrets are loaded from environment variables and are not stored directly in the source code.

### Authorization

Users can only access their own monitors and incident history.

Requests for another user's resources return `404`.

### SSRF Protection

Monitor URLs are validated before requests are made.

The application blocks targets such as:

- `localhost`
- `127.0.0.1`
- Private network addresses
- Link-local addresses
- Cloud metadata addresses
- IPv6 loopback addresses
- URLs containing credentials
- Non-HTTP/HTTPS schemes

Redirect following is disabled during monitor checks.

## Project Structure

```text
statusnest/
├── alembic/
├── app/
│   ├── api/
│   ├── core/
│   ├── db/
│   ├── models/
│   ├── services/
│   ├── main.py
│   ├── tasks.py
│   └── worker.py
├── tests/
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── pytest.ini
├── requirements.txt
└── requirements-dev.txt
```

## Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Then configure the values inside `.env`.

Example:

```env
JWT_SECRET_KEY=replace-with-a-long-random-secret

MYSQL_ROOT_PASSWORD=replace-with-root-password
MYSQL_DATABASE=statusnest
MYSQL_USER=statusnest
MYSQL_PASSWORD=replace-with-db-password

DATABASE_URL=mysql+asyncmy://statusnest:replace-with-db-password@db:3306/statusnest
DATABASE_SYNC_URL=mysql+pymysql://statusnest:replace-with-db-password@db:3306/statusnest

CELERY_BROKER_URL=redis://redis:6379/0
```

Generate a secure JWT secret with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Never commit your real `.env` file.

## Running with Docker

Build and start the application:

```bash
docker compose up --build -d
```

Check the running services:

```bash
docker compose ps
```

The following services should be running:

```text
api
worker
beat
db
redis
```

The API is available at:

```text
http://localhost:8000
```

Swagger documentation:

```text
http://localhost:8000/docs
```

## Database Migrations

Run Alembic migrations with:

```bash
docker compose exec api alembic upgrade head
```

Create a new migration after changing database models:

```bash
docker compose exec api alembic revision --autogenerate -m "migration description"
```

## Tests

Activate the local virtual environment:

```bash
source .venv/bin/activate
```

Install development dependencies:

```bash
python -m pip install -r requirements-dev.txt
```

Run all tests:

```bash
pytest -v
```

The current backend MVP includes automated tests for:

- SSRF protection
- Local and private address blocking
- Unsafe URL formats
- Public URL validation
- Incident authorization
- Monitor owner access
- Incident lifecycle behavior

## Main API Capabilities

### Authentication

```text
Register
Login
Current user
```

### Monitors

```text
Create monitor
List monitors
Get monitor
Update monitor
Delete monitor
Manual check
Check history
Statistics
Incident history
```

### Background Monitoring

Active monitors are periodically scheduled by Celery Beat and processed by Celery workers.

## Development Status

### v0.1.0 — Backend MVP

Completed:

- Core API
- Authentication
- Authorization
- Monitor CRUD
- Website checking
- Scheduled monitoring
- Check history
- Statistics
- Incident detection and recovery
- Basic SSRF protection
- Automated tests
- Docker development environment
- Environment-based configuration

Future versions may include:

- Email or webhook notifications
- Rate limiting
- More extensive integration tests
- Improved observability and structured logging
- Advanced SSRF protections
- Production deployment hardening
- Public status pages

## Disclaimer

StatusNest `v0.1.0` is a backend MVP and portfolio project.

Additional security hardening and operational configuration should be completed before exposing the service to untrusted public traffic.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.