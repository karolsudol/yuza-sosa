import os
import sys
from airflow.models import DagBag


def validate_dags():
    dag_folder = os.path.expanduser("dags")
    dag_bag = DagBag(dag_folder)

    if dag_bag.import_errors:
        print("DAG Import Errors:")
        for dag_id, error in dag_bag.import_errors.items():
            print(f"{dag_id}: {error}")
        sys.exit(1)
    else:
        print("All DAGs are valid!")


if __name__ == "__main__":
    validate_dags()
