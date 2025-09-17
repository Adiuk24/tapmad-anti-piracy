# Tapmad Anti-Piracy System Makefile
# Provides convenient commands for development and deployment

.PHONY: help install dev test lint format clean migrate api worker crawl e2e status health

# Default target
help:
	@echo "Tapmad Anti-Piracy System - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  install     - Install dependencies and setup environment"
	@echo "  dev         - Install + setup pre-commit hooks"
	@echo "  test        - Run tests"
	@echo "  lint        - Run linting (ruff, black, mypy)"
	@echo "  format      - Format code (black, ruff)"
	@echo "  clean       - Clean up temporary files"
	@echo ""
	@echo "Database:"
	@echo "  migrate     - Run database migrations"
	@echo "  migrate-create - Create new migration"
	@echo ""
	@echo "Services:"
	@echo "  api         - Start API server"
	@echo "  worker      - Start Celery worker"
	@echo "  crawl       - Run YouTube crawler"
	@echo ""
	@echo "Monitoring:"
	@echo "  status      - Show system status"
	@echo "  health      - Check system health"
	@echo "  logs        - Show recent logs"
	@echo ""
	@echo "Testing:"
	@echo "  e2e         - Run end-to-end tests"
	@echo "  test-unit   - Run unit tests only"
	@echo "  test-integration - Run integration tests only"

# Development setup
install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt
	@echo "✅ Dependencies installed"

dev: install
	@echo "Setting up development environment..."
	pre-commit install
	@echo "✅ Development environment ready"

# Code quality
test:
	@echo "Running tests..."
	pytest tests/ -v --tb=short
	@echo "✅ Tests completed"

lint:
	@echo "Running linters..."
	ruff check src/ tests/
	black --check src/ tests/
	mypy src/
	@echo "✅ Linting completed"

format:
	@echo "Formatting code..."
	black src/ tests/
	ruff check --fix src/ tests/
	@echo "✅ Code formatted"

clean:
	@echo "Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	find . -type d -name ".mypy_cache" -delete
	rm -rf build/ dist/ *.egg-info/
	@echo "✅ Cleanup completed"

# Database operations
migrate:
	@echo "Running database migrations..."
	alembic upgrade head
	@echo "✅ Migrations completed"

migrate-create:
	@echo "Creating new migration..."
	@read -p "Enter migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"
	@echo "✅ Migration created"

# Service management
api:
	@echo "Starting API server..."
	uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
	@echo "✅ API server started"

worker:
	@echo "Starting Celery worker..."
	celery -A src.enforce.emailer worker --loglevel=info
	@echo "✅ Celery worker started"

crawl:
	@echo "Running YouTube crawler..."
	python -m src.crawler.main --platform youtube --keywords "cricket live" "football match" --max-results 10
	@echo "✅ Crawler completed"

# Monitoring
status:
	@echo "System Status:"
	@echo "=============="
	@echo "Database: $$(python -c "from src.shared.database import test_connection; print('✅ Connected' if test_connection() else '❌ Disconnected')")"
	@echo "Redis: $$(python -c "from src.shared.redis_client import get_redis; print('✅ Connected' if get_redis().ping() else '❌ Disconnected')")"
	@echo "Environment: $$(python -c "from src.shared.config import settings; print(settings.env)")"
	@echo "Dry Run Mode: $$(python -c "from src.shared.config import settings; print('✅ Enabled' if settings.enforcement_dry_run else '❌ Disabled')")"

health:
	@echo "Health Check:"
	@echo "============="
	@python -c "from src.shared.metrics import get_health_status; import json; print(json.dumps(get_health_status(), indent=2))"

logs:
	@echo "Recent logs:"
	@echo "============"
	@tail -n 50 logs/app.log 2>/dev/null || echo "No log file found"

# Testing
e2e:
	@echo "Running end-to-end tests..."
	pytest tests/test_e2e.py -v
	@echo "✅ E2E tests completed"

test-unit:
	@echo "Running unit tests..."
	pytest tests/test_*.py -k "not test_e2e" -v
	@echo "✅ Unit tests completed"

test-integration:
	@echo "Running integration tests..."
	pytest tests/test_integration.py -v
	@echo "✅ Integration tests completed"

# Pipeline operations
pipeline-run:
	@echo "Running complete pipeline..."
	@read -p "Enter keywords (comma-separated): " keywords; \
	python -c "import requests; import json; response = requests.post('http://localhost:8000/pipeline/run', json={'keywords': [k.strip() for k in '$$keywords'.split(',')], 'max_results': 5}); print(json.dumps(response.json(), indent=2))"
	@echo "✅ Pipeline completed"

# Docker operations (if using Docker)
docker-build:
	@echo "Building Docker image..."
	docker build -t tapmad-antipiracy .
	@echo "✅ Docker image built"

docker-run:
	@echo "Running Docker container..."
	docker run -p 8000:8000 --env-file .env tapmad-antipiracy
	@echo "✅ Docker container started"

# Quick start for new developers
quickstart: dev migrate
	@echo "Quick start completed!"
	@echo "Next steps:"
	@echo "1. Copy .env.example to .env and configure"
	@echo "2. Start services: make api (in one terminal) and make worker (in another)"
	@echo "3. Test the system: make pipeline-run"
	@echo "4. Check status: make status"

# Production deployment
deploy:
	@echo "Deploying to production..."
	@echo "⚠️  Make sure to:"
	@echo "1. Set ENV=production in .env"
	@echo "2. Configure real API keys"
	@echo "3. Set ENFORCEMENT_DRY_RUN=false"
	@echo "4. Run: make migrate"
	@echo "5. Start services with production settings"
	@echo "✅ Deployment checklist completed"
