.ONESHELL:
.PHONY: help clean check sourcery mypy
.DEFAULT_GOAL := run

BIND_IP ?= 192.168.1.85
PORT ?= 8000


# PYTHON = ./.venv/bin/python
PYTHON = python
# PIP = ./.venv/bin/pip
PIP = pip
MAIN_FOLDER = project

help: ## display this help message
	@echo "Please use \`\033[32mmake \033[36m<target>\033[0m'\nList of \033[36m<targets>\033[0m with dependencies and \033[35mdescription\033[0m:"
	@awk -F '[:#]' '/^[\.\/a-zA-Z]+:.*#/ && NF>=2 {printf "\033[36m  %-25s\033[0m %-20s \033[35m %s \033[0m\n", $$1, $$2, $$4}' $(MAKEFILE_LIST) | sort

.venv/bin/activate: requirements.txt  ## install virtual environment
	python -m venv .venv
	. .venv/bin/activate
	$(PIP) install -r requirements.txt

venv: .venv/bin/activate ## activate virtual environment
	. .venv/bin/activate

run: venv ## run the app
	. .venv/bin/activate && cd $(MAIN_FOLDER) && $(PYTHON) main.py

serve: venv  ## run the app in browser
	pygbag --ume_block 0 --template utils/black.tmpl --icon $(MAIN_FOLDER)/assets/icon.png --no_opt --bind $(BIND_IP) --port $(PORT) $(MAIN_FOLDER)

update_schema: venv ## generate pydantic model schema and save it to: project/config_model/config_schema.json
	. .venv/bin/activate && cd $(MAIN_FOLDER)/config_model && $(PYTHON) config_pydantic.py

check: sourcery mypy  ##  run all checks

sourcery: venv ## check for code smells and generate suggestions
	sourcery review $(MAIN_FOLDER)

mypy: venv ## run mypy static type checker
	mypy --config-file pyproject.toml $(MAIN_FOLDER)

clean:  ## remove virtual environment
	rm -rf venv
