from datetime import timedelta

# The DAG object; we'll need this to instantiate a DAG
from airflow import DAG

# Operators; we need this to operate!
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago


def test_function():
    print("COOL VALUE")


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email': ['airflow@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}
dag = DAG(
    'dag_script',
    default_args=default_args,
    description='Simple dag_script',
    schedule_interval=timedelta(days=1),
    start_date=days_ago(2),
    tags=['dag_script'],
)
