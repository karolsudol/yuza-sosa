"""
This module contains an Airflow DAG for copying data from bundlers.csv to PostgreSQL.
"""

from datetime import datetime, timedelta
import pandas as pd
from airflow.hooks.base import BaseHook
from airflow.exceptions import AirflowException

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


def copy_csv_to_postgres(**kwargs):
    """Read data from bundlers.csv and store it in PostgreSQL."""
    csv_file_path = "/opt/airflow/data/bundlers.csv"  # Updated path
    df = pd.read_csv(csv_file_path)

    # Ensure the column is named 'addresses'
    if "addresses" not in df.columns:
        df.columns = ["addresses"]

    pg_hook = PostgresHook(postgres_conn_id="postgres_default")
    df.to_sql(
        "addresses",
        pg_hook.get_sqlalchemy_engine(),
        if_exists="replace",
        index=False,
    )


if AIRFLOW_AVAILABLE:
    default_args = {
        "owner": "airflow",
        "depends_on_past": False,
        "start_date": datetime(2024, 7, 24),
        "email_on_failure": False,
        "email_on_retry": False,
        "retries": 0,
        "retry_delay": timedelta(minutes=5),
    }

    dag = DAG(
        "copy_csv_to_postgres",
        default_args=default_args,
        description="A DAG to copy data from bundlers.csv to PostgreSQL",
        schedule_interval="0 9 * * *",
        catchup=False,
    )

    check_connection = PythonOperator(
        task_id="check_postgres_connection",
        python_callable=check_postgres_connection,
        dag=dag,
    )

    copy_csv_task = PythonOperator(
        task_id="copy_csv_to_postgres",
        python_callable=copy_csv_to_postgres,
        provide_context=True,
        dag=dag,
    )

    check_connection >> copy_csv_task

else:
    print("Airflow not available. DAG not created.")

if __name__ == "__main__":
    check_postgres_connection()
    copy_csv_to_postgres()
