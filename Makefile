PYTHON_VERSION = 3.9

all:	help

help:
	@echo "> help: Show this"
	@echo "> lint: Run linters"
	@echo "> test: Run tests"
	@echo "> docker: Run linters and tests in Docker (default PYTHON_VERSION=$(PYTHON_VERSION))"

lint:
	mypy genbu tests --strict --no-warn-unused-ignores
	pylint genbu tests
	flake8 genbu tests --max-complexity=7

test:
	pytest --cov=genbu --cov=tests --cov-report=term-missing --cov-fail-under=90 --cov-branch -x --hypothesis-verbosity=verbose

dist:
	python setup.py sdist bdist_wheel

docker:
	docker build -t test-genbu --build-arg PYTHON_IMAGE=python:$(PYTHON_VERSION)-alpine .
	docker run test-genbu

.PHONY:	all dist docker help lint test
