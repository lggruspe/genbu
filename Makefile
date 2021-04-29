all:	help

help:
	@echo "> help: Show this"
	@echo "> lint: Run linters"
	@echo "> test: Run tests"

lint:
	pylint infer_parser
	flake8 --max-complexity=7 infer_parser
	mypy --strict infer_parser

test:
	pytest --cov=infer_parser --cov-report=term-missing

dist:
	python setup.py sdist bdist_wheel

.PHONY:	all dist help lint test
