venv:
	# Create virtual environment.
	python3.10 -m venv venv
	./venv/bin/pip3 install --upgrade pip setuptools wheel
	./venv/bin/pip3 install -r requirements.txt

test:
	# Run pytest.
	./venv/bin/pytest -s --cov=src/flask_first tests/

format:
	# Run checking and formatting sources.
	./venv/bin/pre-commit run -a

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
