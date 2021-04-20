all:

lint:
	pylint infer_parser.py
	flake8 --max-complexity=5 infer_parser.py
	mypy infer_parser.py

test:
	pytest --cov=infer_parser test_infer_parser.py --cov-report=term-missing

.PHONY:	all lint test
