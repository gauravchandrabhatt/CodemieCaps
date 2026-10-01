.PHONY: install run test build
install:
	python -m pip install -e '.[test]'
run:
	uvicorn codemie_caps.main:app --app-dir src --reload

test:
	python -m pytest --junitxml=test-results/junit.xml
build:
	python -m compileall -q src tests
	python -m pip wheel --no-deps --wheel-dir dist .
