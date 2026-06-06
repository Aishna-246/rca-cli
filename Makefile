.PHONY: test security lint all

test:
	pytest tests/ -v --cov=rca --cov-report=term-missing

security:
	bandit -r rca/ -ll
	semgrep --config=p/python rca/ --quiet

lint:
	python -m py_compile rca/**/*.py

all: test security lint