import pytest
from airflow.models import DagBag, TaskInstance
from airflow.utils.state import State
from datetime import datetime


@pytest.fixture(scope="session")
def dag_bag():
    return DagBag()


def test_user_operations_analysis_dag(dag_bag):
    dag = dag_bag.get_dag(dag_id="user_operations_analysis")
    assert dag is not None
    assert len(dag.tasks) == 2


def test_check_postgres_connection(dag_bag):
    dag = dag_bag.get_dag(dag_id="user_operations_analysis")
    task = dag.get_task(task_id="check_postgres_connection")

    ti = TaskInstance(task=task, execution_date=datetime.now())
    ti.run(ignore_ti_state=True)  # Ensure it runs the task
    assert ti.state == State.SUCCESS


def test_get_dune_data(dag_bag):
    dag = dag_bag.get_dag(dag_id="user_operations_analysis")
    task = dag.get_task(task_id="get_dune_data")

    ti = TaskInstance(task=task, execution_date=datetime.now())
    ti.run(ignore_ti_state=True)  # Ensure it runs the task
    assert ti.state == State.SUCCESS
