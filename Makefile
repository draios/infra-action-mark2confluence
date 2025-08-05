.PHONY: help install-poetry install-pipenv sync-poetry sync-pipenv test clean

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install-poetry: ## Install Poetry
	@echo "Installing Poetry..."
	curl -sSL https://install.python-poetry.org | python3 -

install-pipenv: ## Install Pipenv
	@echo "Installing Pipenv..."
	pip install pipenv

sync-poetry: ## Update Poetry dependencies from requirements.txt
	poetry install --no-root
	@while read -r line; do \
		if [ -n "$$line" ] && [ "$${line:0:1}" != "#" ]; then \
			poetry add "$$line"; \
		fi; \
	done < requirements.txt

sync-pipenv: ## Update Pipenv dependencies from requirements.txt
	pipenv install -r requirements.txt

test: ## Run tests
	pytest tests/

clean: ## Clean up build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete
