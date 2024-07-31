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

# Constants
DUNE_API_KEY = Variable.get("DUNE_API_KEY")
DUNE_QUERY_ID_USER_OPERATIONS = 3953351  # User operations query ID
DUNE_QUERY_ID_BUNDLER_TRANSACTIONS = 3955394  # Bundler transactions query ID

# Calculate previous day's date in UTC
PREVIOUS_DAY = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
START_DATE = PREVIOUS_DAY

# DAG configurations
DAG_NAME = "user_operations_analysis"
DEFAULT_ARGS = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 7, 24),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 0,
    "retry_delay": timedelta(minutes=5),
}
SCHEDULE_INTERVAL = "0 9 * * *"

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


def fetch_dune_data(query_id, table_name, **kwargs):
    """Fetch data from Dune Analytics and store it in PostgreSQL."""
    query = QueryBase(
        name=table_name,
        query_id=query_id,
        params=[
            QueryParameter.text_type(name="StartDate", value=START_DATE),
            QueryParameter.text_type(name="EndDate", value=START_DATE),
        ],
    )
    dune = DuneClient(api_key=DUNE_API_KEY, request_timeout=600)
    results_df = dune.run_query_dataframe(query)

    pg_hook = PostgresHook(postgres_conn_id="postgres_default")
    results_df.to_sql(
        table_name, pg_hook.get_sqlalchemy_engine(), if_exists="replace", index=False
    )


def fetch_addresses_and_match_transactions(**kwargs):
    """Fetch addresses from PostgreSQL and match transactions from Dune Analytics."""
    pg_hook = PostgresHook(postgres_conn_id="postgres_default")
    engine = pg_hook.get_sqlalchemy_engine()

    # Fetch addresses from PostgreSQL
    addresses_df = pd.read_sql("SELECT addresses FROM addresses", engine)
    addresses_list = addresses_df["addresses"].tolist()
    addresses_param = ",".join(addresses_list)

    # Fetch and store bundler transactions
    query = QueryBase(
        name="Bundler Transactions",
        query_id=DUNE_QUERY_ID_BUNDLER_TRANSACTIONS,
        params=[
            QueryParameter.text_type(name="StartDate", value=START_DATE),
            QueryParameter.text_type(name="EndDate", value=START_DATE),
            QueryParameter.text_type(name="TransactionSenders", value=addresses_param),
        ],
    )
    dune = DuneClient(api_key=DUNE_API_KEY, request_timeout=600)
    bundler_transactions_df = dune.run_query_dataframe(query)
    bundler_transactions_df.to_sql(
        "bundler_transactions", engine, if_exists="replace", index=False
    )


def merge_transactions(**kwargs):
    """Merge user_operations with bundler_transactions and create final_results table."""
    pg_hook = PostgresHook(postgres_conn_id="postgres_default")
    engine = pg_hook.get_sqlalchemy_engine()

    user_operations_df = pd.read_sql("SELECT * FROM user_operations", engine)
    bundler_transactions_df = pd.read_sql(
        "SELECT transaction_hash FROM bundler_transactions", engine
    )

    user_operations_df["category"] = user_operations_df["transaction_hash"].apply(
        lambda x: (
            "biconomy"
            if x in bundler_transactions_df["transaction_hash"].values
            else "other"
        )
    )

    user_operations_df.to_sql("final_results", engine, if_exists="replace", index=False)


def aggregate_final_results(**kwargs):
    """Aggregate final results by hour and category and store in view_final_results."""
    pg_hook = PostgresHook(postgres_conn_id="postgres_default")
    engine = pg_hook.get_sqlalchemy_engine()

    query = """
    SELECT
        DATE_TRUNC('hour', block_time::timestamp) AS hour,
        category,
        COUNT(*) AS operation_count
    FROM
        final_results
    GROUP BY
        hour, category
    """

    aggregated_df = pd.read_sql(query, engine)

    aggregated_df.to_sql("view_final_results", engine, if_exists="replace", index=False)


if AIRFLOW_AVAILABLE:
    dag = DAG(
        DAG_NAME,
        default_args=DEFAULT_ARGS,
        description="A DAG to analyze user operations from Dune Analytics",
        schedule_interval=SCHEDULE_INTERVAL,
        catchup=False,
    )

    check_postgres_connection_task = PythonOperator(
        task_id="check_postgres_connection",
        python_callable=check_postgres_connection,
        dag=dag,
    )

    fetch_user_operations_task = PythonOperator(
        task_id="fetch_user_operations",
        python_callable=fetch_dune_data,
        op_kwargs={
            "query_id": DUNE_QUERY_ID_USER_OPERATIONS,
            "table_name": "user_operations",
        },
        provide_context=True,
        dag=dag,
    )

    fetch_addresses_and_match_task = PythonOperator(
        task_id="fetch_addresses_and_match_transactions",
        python_callable=fetch_addresses_and_match_transactions,
        provide_context=True,
        dag=dag,
    )

    merge_transactions_task = PythonOperator(
        task_id="merge_transactions",
        python_callable=merge_transactions,
        provide_context=True,
        dag=dag,
    )

    aggregate_final_results_task = PythonOperator(
        task_id="aggregate_final_results",
        python_callable=aggregate_final_results,
        provide_context=True,
        dag=dag,
    )

    (
        check_postgres_connection_task
        >> fetch_user_operations_task
        >> fetch_addresses_and_match_task
        >> merge_transactions_task
        >> aggregate_final_results_task
    )

else:
    print("Airflow not available. DAG not created.")

if __name__ == "__main__":
    check_postgres_connection()
    fetch_dune_data(
        query_id=DUNE_QUERY_ID_USER_OPERATIONS, table_name="user_operations"
    )
    fetch_addresses_and_match_transactions()
    merge_transactions()
    aggregate_final_results()
