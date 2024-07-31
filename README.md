
# yuza-sosa

Airflow scheduler pulling data from Dune, storing it in a Postgres database and creating Grafana Dahbaords.


**Table of Contents**
-------------------
* [Quick Start](#quick-start)
* [Contributing](#contributing)
* [Prerequisites](#prerequisites)
* [Manual Setup](#manual-setup)
* [Project Structure](#project-structure)
* [Customization](#customization)
* [Testing](#testing)
* [Accessing Fetched Data](#accessing-fetched-data)
* [Troubleshooting](#troubleshooting)
* [TODO](#todo)
* [License](#license)


### Quick Start
-------------

To set up and run the entire project, simply execute:

```
chmod +x setup.sh
./setup.sh
```

this will set up the Docker images, initialize Airflow, start Airflow services, and run the DAGs.

with
- airflow on http://localhost:8080/
- graphana on http://localhost:3000/

After running the schedulers dags `copy_csv_to_postgres` and `user_operations_analysis.py` you can access the data in the Grafana dashboards or/and querying the final view table:
```sql
SELECT hour, category, operation_count FROM view_final_results ORDER BY hour;
```

### Contributing
---------------
* Clone the repository
* Create a new branch
* Run `make pre-commit` to run the pre-commit hooks
* Commit messages should be in the following format:
    * `feat: {description}`
    * `fix: {description}`
    * `docs: {description}`
    * `style: {description}`
    * `refactor: {description}`
    * `test: {description}`

* Before merging to `master`, the `develop` branch should be merged into `master`


### Prerequisites
---------------

* Docker
* Docker Compose
* Make

```bash
cp .env-example .env `
```

make sure you set .env with:
```
DUNE_API_KEY={YOUR_KEY}
```


### Manual Setup
-------------

If you prefer to run the commands manually, you can use the following Make commands:

* `make build`: Build the Docker images
* `make init`: Initialize Airflow
* `make up`: Start Airflow services
* `make down`: Stop Airflow services
* `make logs`: View logs
* `make shell`: Access the Airflow shell

### Project Structure
-----------------

* `dags/user_operations_analysis.py.py`: The main Airflow DAG file that pulls data off and on chain
* `dags/validate_dags.py.py`: The helper script to validate the DAGs
* `dags/copy_csv_to_postgres.py`: The helper script to copy the CSV files to the DB
* `dags/google_sheet_to_postgres.py`: The helper script to copy from sheets files to the DB
* `Dockerfile`: Defines the Docker image for Airflow
* `docker-compose.yml`: Defines the services (Airflow, PostgreSQL)
* `requirements.txt`: Lists the Python dependencies
* `Makefile`: Contains shortcuts for common commands
* `setup.sh`: Script to automate the entire setup process

### Customization
-------------

To modify the analysis or add new features:

1. Edit the `dags/daily_etl.py` file
2. Rebuild the Docker images and Restart the services using
```bash
make sync-dags
```
3. If updated dependencies in `requirements.txt` then make sure Airflow has the latest dependencies by running:
```bash
make build
make down
make up
```

### Testing
------

This project includes both unit tests and end-to-end tests for the Airflow DAG.

* `make test`: Run all tests
* `make test-unit`: Run only unit tests
* `make test-e2e`: Run only end-to-end tests

### Accessing Fetched Data
---------------------

To access the DB data:

1. `docker exec -it yuza-sosa-postgres-1 bash`
2. `psql -U airflow -d airflow`
3. or `psql -h localhost -p 5433 -U airflow -d airflow`
3. `SELECT * FROM user_operations LIMIT 10;`
4. `select * from view_final_results;`

### Troubleshooting
-----------------

If you encounter any issues:

1. Check the logs using `make logs`
2. Ensure all required ports are available (8080 for Airflow webserver)
3. Try stopping all services with `make down`, then start again with `make up`
4. Create dags, logs and plugins folder inside the project directory
5. Set user permissions for Airflow to your current user ex:
```bash
sudo chown -R airflow:airflow /opt/airflow
```
5. If fails, set manually `DUNE_API_KEY` can be done in airflow.cfg or console
6. check export paths in modules are not recognised
```bash
export PYTHONPATH=dags/:$PYTHONPATH
```

### TODO
------
- set `google_sheet_to_postgres` with service_accout_key
- better naming convention for DAGs and tables
- validate and add more tests
- add more dashboards
- partition tables


### License
-------

MIT License
