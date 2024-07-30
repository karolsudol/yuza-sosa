"""
This module contains an Airflow DAG for analyzing UserOperation events.
It fetches data from Dune Analytics, processes it, and stores the results in PostgreSQL.
"""

from datetime import datetime, timedelta
from airflow.hooks.base import BaseHook
from airflow.exceptions import AirflowException

PREVIOUS_DAY = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
    from airflow.providers.postgres.hooks.postgres import PostgresHook

    AIRFLOW_AVAILABLE = True
except ImportError:
    AIRFLOW_AVAILABLE = False
    print("Airflow not available. Running in local mode.")


def check_postgres_connection():
    """Check if the PostgreSQL connection is valid."""
    try:
        conn = BaseHook.get_connection("postgres_default")
        print(f"Connection {conn.conn_id} is valid.")
    except AirflowException as e:
        print(f"Connection error: {str(e)}")
        raise


def print_execution_date(execution_date):
    """Print the execution date."""
    print(f"Execution date: {execution_date}")


if AIRFLOW_AVAILABLE:
    default_args = {
        "owner": "airflow",
        "depends_on_past": False,
        "start_date": datetime(2024, 7, 31),
        "email_on_failure": False,
        "email_on_retry": False,
        "retries": 0,
        "retry_delay": timedelta(minutes=5),
    }

    dag = DAG(
        "ETL",
        default_args=default_args,
        description="A DAG to analyze UserOperation events.",
        schedule_interval="0 9 * * *",  # Every day at 9am
        catchup=False,
    )

    check_connection = PythonOperator(
        task_id="check_postgres_connection",
        python_callable=check_postgres_connection,
        dag=dag,
    )

    print_execution_date_task = PythonOperator(
        task_id="print_execution_date",
        python_callable=print_execution_date,
        op_args=[PREVIOUS_DAY],  # Pass the argument here
        dag=dag,
    )

    check_connection >> print_execution_date_task

else:
    print("Airflow not available. DAG not created.")

if __name__ == "__main__":
    print_execution_date(PREVIOUS_DAY)
