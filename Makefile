# define the name of the virtual environment directory
VENV := venv

# default target, when make executed without arguments
all: venv

$(VENV)/bin/activate: requirements.txt
	python3 -m venv $(VENV)
	./$(VENV)/bin/pip3 install -r requirements.txt

# venv is a shortcut target
venv: $(VENV)/bin/activate

pylint: venv
	./$(VENV)/bin/pylint --disable=C0303,R0903,R0915,C0103,E1101,E0102,R0913,W0123,R0912,R0801,W0622 --extension-pkg-whitelist='pydantic' app

tests: venv
	./$(VENV)/bin/pytest -q app/tests/test_api.py -q app/tests/test_utils.py

coverage: venv
	./$(VENV)/bin/coverage run -m pytest -q app/tests/test_api.py -q app/tests/test_utils.py && ./$(VENV)/bin/coverage report -m

run: venv
	./$(VENV)/bin/uvicorn app.main:app --host localhost --port 8000 --reload

package: venv
	./$(VENV)/bin/python -m pip install --upgrade build
	./$(VENV)/bin/python -m build

start-db: venv
	docker-compose up -d

clean:
	rm -rf $(VENV)
	find . -type f -name '*.pyc' -delete

# make sure that all targets are used/evaluated even if a file with same name exists
.PHONY: all venv run clean tests
