lint:
	mypy tortoise --strict
	pylint tortoise
	flake8 tortoise --max-complexity=7

.PHONY:	lint
