VENV = venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

include .env
export

$(VENV)/bin/activate: requirements.txt
	python3 -m venv $(VENV)
	$(PIP) install -r requirements.txt

test-unit: $(VENV)/bin/activate
	# $(PYTHON) -m unittest tests/test_ETL.py

.PHONY: build up down logs shell init run all grafana-logs grafana-shell clean

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

shell:
	docker-compose exec airflow-webserver bash

init:
	docker-compose up -d postgres
	docker-compose run --rm airflow-webserver airflow db init
	docker-compose run --rm airflow-webserver airflow users create --username $(AIRFLOW_WWW_USER_USERNAME) --firstname Admin --lastname User --role Admin --email admin@example.com --password $(AIRFLOW_WWW_USER_PASSWORD)
	docker-compose down

run:
	docker-compose up

grafana-logs:
	docker-compose logs -f grafana

grafana-shell:
	docker-compose exec grafana /bin/bash

clean:
	docker-compose down -v
	rm -rf $(VENV)

all: build up