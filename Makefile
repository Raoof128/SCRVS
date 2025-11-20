.PHONY: help install install-dev test lint format clean scan score docs

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install the package
	pip install -e .

install-dev: ## Install package with development dependencies
	pip install -e ".[dev]"
	pre-commit install

test: ## Run tests
	pytest --cov=solidity_scanner --cov-report=term --cov-report=html

test-verbose: ## Run tests with verbose output
	pytest -v --cov=solidity_scanner --cov-report=term --cov-report=html

test-fast: ## Run tests without coverage
	pytest

lint: ## Run linting checks
	flake8 --max-line-length=100 --extend-ignore=E203,W503 solidity_scanner tests
	mypy --ignore-missing-imports solidity_scanner || true
	bandit -r solidity_scanner || true

format: ## Format code with black and isort
	black --line-length=100 solidity_scanner tests
	isort --profile=black --line-length=100 solidity_scanner tests

format-check: ## Check code formatting without making changes
	black --check --line-length=100 solidity_scanner tests
	isort --check-only --profile=black solidity_scanner tests

clean: ## Clean generated files
	find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -r {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete
	find . -type f -name "coverage.xml" -delete
	find . -type f -name "*_report.json" -delete
	find . -type f -name "*_findings.csv" -delete
	find . -type f -name "*_security_audit.md" -delete
	rm -rf dist build *.egg-info

scan: ## Scan example vulnerable contract
	python -m solidity_scanner.cli scan examples/vulnerable.sol

scan-safe: ## Scan example safe contract
	python -m solidity_scanner.cli scan examples/safe.sol

score: ## Calculate security score for vulnerable contract
	python -m solidity_scanner.cli score examples/vulnerable.sol

docs: ## Generate documentation (if applicable)
	@echo "Documentation is in markdown files: README.md, ARCHITECTURE.md, etc."

pre-commit: ## Run pre-commit hooks on all files
	pre-commit run --all-files

ci: lint test ## Run CI checks locally
	@echo "All CI checks passed!"

all: clean install-dev lint test ## Clean, install, lint, and test
	@echo "Setup complete!"

