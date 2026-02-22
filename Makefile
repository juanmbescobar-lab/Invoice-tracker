.PHONY: help setup run test lint format clean docker-build docker-run docker-stop

.DEFAULT_GOAL := help

# Variables
APP_NAME := invoicetrack
PORT := 8000

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Create venv and install dependencies
	python3 -m venv .venv
	. .venv/bin/activate && pip install --upgrade pip
	. .venv/bin/activate && pip install -e ".[dev]"
	@echo "Done! Activate with: source .venv/bin/activate"

run: ## Run the app locally
	. .venv/bin/activate && uvicorn src.main:app --reload --host 0.0.0.0 --port $(PORT)

test: ## Run tests with coverage
	. .venv/bin/activate && pytest tests/ -v --tb=short --cov=src --cov-report=term-missing

lint: ## Run linter
	. .venv/bin/activate && ruff check src/ tests/

format: ## Auto-format code
	. .venv/bin/activate && ruff format src/ tests/

check: lint test ## Run lint + tests (use before PR)

docker-build: ## Build Docker image
	docker build -t $(APP_NAME):latest .

docker-run: docker-build ## Build and run in Docker
	docker run -d --name $(APP_NAME) -p $(PORT):$(PORT) --env-file .env $(APP_NAME):latest
	@echo "Running at http://localhost:$(PORT)"

docker-stop: ## Stop and remove container
	docker stop $(APP_NAME) 2>/dev/null || true
	docker rm $(APP_NAME) 2>/dev/null || true

clean: ## Remove caches and venv
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf .venv build dist *.egg-info .coverage htmlcov