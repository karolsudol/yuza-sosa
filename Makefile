VENV = venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

include .env
export

.PHONY: build up down logs shell init run all grafana-logs grafana-shell clean sync-dags restart-airflow pre-commit test-unit

$(VENV)/bin/activate: requirements.txt
	python3 -m venv $(VENV)
	$(PIP) install -r requirements.txt

test-unit: $(VENV)/bin/activate
	$(PYTHON) -m unittest test_user_operations_analysis.py

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

pre-commit:
	pre-commit install
	pre-commit run --all-files

sync-dags:
	docker cp dags/. yuza-sosa-airflow-webserver-1:/opt/airflow/dags
	$(MAKE) restart-airflow

restart-airflow:
	docker-compose restart airflow-webserver
	docker-compose restart airflow-scheduler

shell:
	docker-compose exec airflow-webserver bash

init:
	docker-compose up -d postgres
	docker-compose run --rm --user "${AIRFLOW_UID}:0" airflow-webserver airflow db init
	docker-compose run --rm --user "${AIRFLOW_UID}:0" airflow-webserver airflow users create --username $(AIRFLOW_WWW_USER_USERNAME) --firstname Admin --lastname User --role Admin --email admin@example.com --password $(AIRFLOW_WWW_USER_PASSWORD)
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

# all: ./setup.sh
all: build up
