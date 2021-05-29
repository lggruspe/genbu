lint:
	mypy genbu --strict
	pylint genbu
	flake8 genbu --max-complexity=7

.PHONY:	lint
