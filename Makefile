PYTHON_IMAGE=python:3.9-alpine

all:	help

# lint: Run linters
lint:
	mypy genbu tests --strict
	pylint genbu tests
	flake8 genbu tests --max-complexity=7

# test: Run tests
test:
	pytest --cov=genbu --cov=tests --cov-report=term-missing --cov-fail-under=90 --cov-branch -x

# help: Show make targets
help:
	@grep '^# \w\+: .\+$$' Makefile | sed 's/^# \(\w\+\: .\+\)$$/> \1/'

# docker: Run linters and tests in Docker container (default PYTHON_IMAGE=python:3.9-alpine)
docker:
	docker build -t test-genbu --build-arg PYTHON_IMAGE=$(PYTHON_IMAGE) .
	docker run test-genbu


.PHONY:	help lint test docker
