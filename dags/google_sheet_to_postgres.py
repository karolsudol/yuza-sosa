from datetime import datetime, timedelta
import pandas as pd
import gspread
from airflow.models import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook

# Google Sheets URL and sheet name
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1QJEYDOr-AMD2bNAoupfjQJYJabFgdb2TRSyekdIfquM/edit?gid=0"
SHEET_NAME = "Bundlers"  # Adjust as necessary

# PostgreSQL table name
POSTGRES_TABLE = "bundlers"

# Define default arguments for the DAG
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 8, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

# Define the DAG
dag = DAG(
    "google_sheet_to_postgres",
    default_args=default_args,
    description="Fetch data from Google Sheets and insert into PostgreSQL",
    schedule_interval=timedelta(days=1),
    catchup=False,
)


def fetch_google_sheet_data():
    """Fetch data from Google Sheets."""
    # Access the public Google Sheet
    client = (
        gspread.Client()
    )  # Use the default credentials https://docs.gspread.org/en/latest/oauth2.html#service-account
    sheet = client.open_by_url(
        GOOGLE_SHEET_URL
    ).sheet1  # Use sheet1 to get the first sheet directly

    # Read the entity names starting from B6 and addresses starting from B7
    entity_names = sheet.col_values(2)[5:]  # Starting from B6
    addresses = sheet.col_values(2)[6:]  # Starting from B7

    # Create a DataFrame from the extracted data
    df = pd.DataFrame(
        {"Entity Name": entity_names[: len(addresses)], "Address": addresses}
    )

    # Save DataFrame to CSV (temporary storage)
    df.to_csv("/tmp/sheet_data.csv", index=False)


def insert_data_into_postgres():
    """Insert data from CSV into PostgreSQL."""
    pg_hook = PostgresHook(postgres_conn_id="postgres_default")
    engine = pg_hook.get_sqlalchemy_engine()

    # Read the data from CSV
    df = pd.read_csv("/tmp/sheet_data.csv")

    # Insert the data into PostgreSQL
    df.to_sql(
        POSTGRES_TABLE,
        engine,
        if_exists="replace",  # Change to 'append' if  not to replace the table every time
        index=False,
    )


# Define the tasks
fetch_task = PythonOperator(
    task_id="fetch_google_sheet_data",
    python_callable=fetch_google_sheet_data,
    dag=dag,
)

insert_task = PythonOperator(
    task_id="insert_data_into_postgres",
    python_callable=insert_data_into_postgres,
    dag=dag,
)

# Set the task dependencies
fetch_task >> insert_task
