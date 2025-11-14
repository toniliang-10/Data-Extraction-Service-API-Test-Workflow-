# Data Extraction Service - Backend API

A Django REST API for managing data extraction jobs from third-party services with comprehensive test coverage.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

## Setup Instructions

### 1. Clone and Navigate to Project

```bash
cd "/Users/toniliang/Desktop/coding Scratch/Data-Extraction-Service-API-Test-Workflow-"
```

### 2. Create and Activate Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install production dependencies
pip install -r requirements.txt

# Install test dependencies
pip install -r requirements-test.txt
```

### 4. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env if needed (default values work for development)
```

### 5. Initialize Database

```bash
# Run database migrations
python manage.py migrate

# (Optional) Create superuser for Django admin
python manage.py createsuperuser
```

## Usage Instructions

### Running the Development Server

```bash
python manage.py runserver
```

The server will start at **http://127.0.0.1:8000/**

### Accessing the Application

- **API Documentation (Swagger UI)**: http://127.0.0.1:8000/api/docs/
- **API Documentation (ReDoc)**: http://127.0.0.1:8000/api/redoc/
- **Django Admin**: http://127.0.0.1:8000/admin/
- **Health Check**: http://127.0.0.1:8000/api/v1/health

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/scan/start` | POST | Start new extraction job |
| `/api/v1/scan/status/<job_id>` | GET | Get job status |
| `/api/v1/scan/result/<job_id>` | GET | Get extraction results |
| `/api/v1/scan/cancel/<job_id>` | POST | Cancel running job |
| `/api/v1/scan/remove/<job_id>` | DELETE | Remove job and results |
| `/api/v1/jobs/jobs` | GET | List all jobs |
| `/api/v1/jobs/statistics` | GET | Get job statistics |
| `/api/v1/health` | GET | Health check |

### Example API Usage

**Start an extraction job:**

```bash
curl -X POST http://127.0.0.1:8000/api/v1/scan/start \
  -H "Content-Type: application/json" \
  -d '{
    "api_token": "test_token_valid_12345",
    "record_type": "contacts",
    "name": "My Extraction Job"
  }'
```

**Check job status:**

```bash
curl http://127.0.0.1:8000/api/v1/scan/status/<job_id>
```

**Get extraction results:**

```bash
curl http://127.0.0.1:8000/api/v1/scan/result/<job_id>
```

### Test API Tokens

For testing purposes, use these valid mock API tokens:
- `test_token_valid_12345`
- `valid_api_key_abc`
- `test_access_token_xyz`

## Running Tests

The project includes a comprehensive test suite with 65+ tests covering all endpoints and scenarios.

### Run All Tests

```bash
pytest
```

### Run Specific Test Categories

```bash
# Seeded data tests (fast, deterministic)
pytest -m seeded

# Edge case tests (error handling and validation)
pytest -m edge_case

# Real extraction tests (end-to-end workflows)
pytest -m real_extraction
```

### Run Tests with Coverage Report

```bash
pytest --cov=api --cov=extraction_service --cov-report=html
```

View coverage report:
```bash
open htmlcov/index.html  # macOS
# or
start htmlcov/index.html  # Windows
```

### Run Tests with Verbose Output

```bash
pytest -v
```

### Run Specific Test File

```bash
pytest tests/test_seeded_data.py
pytest tests/test_edge_cases.py
pytest tests/test_real_extraction.py
```

## Project Structure

```
.
├── manage.py                      # Django management script
├── requirements.txt               # Production dependencies
├── requirements-test.txt          # Test dependencies
├── .env.example                   # Environment variables template
├── pytest.ini                     # Pytest configuration
│
├── extraction_service/            # Django project
│   ├── settings/                  # Settings (dev/test/prod)
│   ├── urls.py                    # Main URL configuration
│   └── wsgi.py                    # WSGI configuration
│
├── api/                           # Main API application
│   ├── models.py                  # Database models
│   ├── serializers.py             # DRF serializers
│   ├── views.py                   # API views (8 endpoints)
│   ├── urls.py                    # API URL routing
│   ├── admin.py                   # Django admin
│   ├── services.py                # Business logic
│   └── utils/                     # Utilities
│
└── tests/                         # Test suite (65+ tests)
    ├── test_seeded_data.py        # Seeded data tests
    ├── test_edge_cases.py         # Edge case tests
    ├── test_real_extraction.py    # Real extraction tests
    ├── conftest.py                # Pytest fixtures
    ├── fixtures/                  # Test data fixtures
    ├── mocks/                     # Mock external API
    └── utils/                     # Test utilities
```

## Database

The application uses SQLite by default for development (no additional setup required).

For production, configure PostgreSQL in your `.env` file:

```env
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
```

## Features

- ✅ 8 RESTful API endpoints
- ✅ Django REST Framework with serializers
- ✅ Async job processing with background threads
- ✅ Mock external API integration for testing
- ✅ Comprehensive error handling
- ✅ Input validation
- ✅ Swagger/OpenAPI documentation
- ✅ Django admin interface
- ✅ 65+ tests with full coverage
- ✅ PostgreSQL and SQLite support
- ✅ CORS configuration

## Troubleshooting

**Issue: Module not found errors**
```bash
# Ensure virtual environment is activated
source venv/bin/activate
pip install -r requirements.txt
```

**Issue: Database errors**
```bash
# Reset database
rm db.sqlite3
python manage.py migrate
```

**Issue: Tests failing**
```bash
# Ensure test settings are used
pytest --ds=extraction_service.settings.test
```

## Production Deployment

1. Set `DEBUG=False` in production settings
2. Configure a strong `SECRET_KEY`
3. Set proper `ALLOWED_HOSTS`
4. Use PostgreSQL instead of SQLite
5. Configure static file serving
6. Set up HTTPS/SSL
7. Use Gunicorn or uWSGI as WSGI server

```bash
# Production server example
gunicorn extraction_service.wsgi:application --bind 0.0.0.0:8000
```
