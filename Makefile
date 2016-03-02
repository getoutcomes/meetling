PYTHON = python3
PIP = pip3
BOWER = bower

.PHONY: test
test:
	$(PYTHON) -m unittest

.PHONY: deps
deps:
	$(PIP) install --user -U -r requirements.txt
	$(BOWER) update

.PHONY: deps-dev
deps-dev:
	$(PIP) install --user -U -r requirements-dev.txt

.PHONY: doc
doc:
	sphinx-build doc doc/build

.PHONY: sample
sample:
	scripts/sample.py

.PHONY: help
help:
	@echo "test:     Run all unit tests"
	@echo "deps:     Update the dependencies"
	@echo "deps-dev: Update the development dependencies"
	@echo "doc:      Build the documentation"
	@echo "sample:   Set up some sample data. Warning: All existing data in the database"
	@echo "          will be deleted."
	@echo "          REDISURL: URL of the Redis database. See"
	@echo "                    python3 -m meetling --redis-url command line option."