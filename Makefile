include .env
export

clean:
	find . -type d -name '__pycache__' -exec rm -rf {} +
	rm -rf .pytest_cache .dist chronologix.egg-info .ruff_cache
	find . -type d -name '.ipynb_checkpoints' -exec rm -rf {} +
	find . -type f -name '.DS_Store' -exec rm -rf {} +


test:
	pytest

all: test run