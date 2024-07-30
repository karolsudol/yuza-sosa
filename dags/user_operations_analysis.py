"""
This module contains an Airflow DAG for analyzing UserOperation events.
It fetches data from Dune Analytics, processes it, and stores the results in PostgreSQL.
"""

from datetime import datetime, timedelta
import pandas as pd
from dune_client.types import QueryParameter
from dune_client.client import DuneClient
from dune_client.query import QueryBase
from airflow.models import Variable
from airflow.hooks.base import BaseHook
from airflow.exceptions import AirflowException

DUNE_API_KEY = Variable.get("DUNE_API_KEY")
DUNE_QUERY_ID = 3953351  # Hardcoded query ID

# Calculate previous day's date in UTC
PREVIOUS_DAY = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
START_DATE = PREVIOUS_DAY

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


def get_dune_data(**kwargs):
    """Fetch data from Dune Analytics and store it in PostgreSQL."""
    query = QueryBase(
        name="User Operations",
        query_id=DUNE_QUERY_ID,
        params=[
            QueryParameter.text_type(
                name="StartDate",
                value=START_DATE,
            ),
            QueryParameter.text_type(
                name="EndDate",
                value=START_DATE,
            ),
        ],
    )
    dune = DuneClient(api_key=DUNE_API_KEY, request_timeout=600)

    results_df = dune.run_query_dataframe(query)

    pg_hook = PostgresHook(postgres_conn_id="postgres_default")
    results_df.to_sql(
        "user_operations",
        pg_hook.get_sqlalchemy_engine(),
        if_exists="replace",
        index=False,
    )


def aggregate_data(**kwargs):
    """Aggregate data by date and hour and store it in PostgreSQL."""
    pg_hook = PostgresHook(postgres_conn_id="postgres_default")
    engine = pg_hook.get_sqlalchemy_engine()

    query = """
    SELECT
        DATE_TRUNC('hour', block_time::timestamp) as hour,
        COUNT(*) as operation_count
    FROM
        user_operations
    GROUP BY
        hour
    """

    aggregated_df = pd.read_sql(query, engine)

    aggregated_df.to_sql(
        "aggregated_user_operations",
        engine,
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
        "user_operations_analysis",
        default_args=default_args,
        description="A DAG to analyze user operations from Dune Analytics",
        schedule_interval="0 9 * * *",
        catchup=False,
    )

    check_connection = PythonOperator(
        task_id="check_postgres_connection",
        python_callable=check_postgres_connection,
        dag=dag,
    )

    dune_task = PythonOperator(
        task_id="get_dune_data",
        python_callable=get_dune_data,
        provide_context=True,
        dag=dag,
    )

    aggregate_task = PythonOperator(
        task_id="aggregate_data",
        python_callable=aggregate_data,
        provide_context=True,
        dag=dag,
    )

    check_connection >> dune_task >> aggregate_task

else:
    print("Airflow not available. DAG not created.")

if __name__ == "__main__":
    check_postgres_connection()
    get_dune_data()
    aggregate_data()
