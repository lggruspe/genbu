all:	help

help:
	@echo "> help: Show this"
	@echo "> lint: Run linters"
	@echo "> test: Run tests"

lint:
	pylint infer_parser.py
	flake8 --max-complexity=6 infer_parser.py
	mypy --strict infer_parser.py

test:
	pytest --cov=infer_parser test_infer_parser.py --cov-report=term-missing

.PHONY:	all help lint test
