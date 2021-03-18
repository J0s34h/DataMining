import datetime
from airflow.models import DAG
from airflow.operators.python_operator import PythonOperator

args = {
    'owner': 'airflow',
    'start_date': datetime.datetime(2021, 3, 16),
    'retries': 1,
    'retry_delay': datetime.timedelta(minutes=1),
    'depends_on_past': False,
}


def start():
    print("Dag Function")


with DAG(dag_id='dag_script', default_args=args, schedule_interval=None) as dag:
    dag_script_operator = PythonOperator(
        task_id='dag_script',
        python_callable=start,
        dag=dag
    )
