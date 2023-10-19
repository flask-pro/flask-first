.PHONY: venv test tox format clean build install upload_to_testpypi upload_to_pypi all


venv:
	# Create virtual environment.
	python3.11 -m venv venv
	./venv/bin/pip3 -q install --upgrade pip setuptools wheel
	./venv/bin/pip3 -q install -e ".[dev]"
	./venv/bin/pip3 -q install -e .

format:
	# Run checking and formatting sources.
	./venv/bin/pre-commit run -a

test: venv
	# Run pytest.
	./venv/bin/bandit -q -r src/
	./venv/bin/pytest -s -x --cov-report term-missing:skip-covered --cov=src/flask_first tests/

tox: venv
	# Testing project via several Python versions.
	./venv/bin/tox

clean:
	rm -rf dist/
	rm -rf src/Flask_First.egg-info

build: clean
	python3 -m build

install: build
	./venv/bin/pip install dist/Flask-First-*.tar.gz

upload_to_testpypi: build
	python3 -m twine upload --repository testpypi dist/*

upload_to_pypi: build
	python3 -m twine upload --repository pypi dist/*

all: venv tox build
