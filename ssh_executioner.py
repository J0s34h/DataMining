import datetime
from airflow.models import DAG
from airflow.operators.bash import BashOperator

args = {
    'owner': 'airflow',
    'start_date': datetime.datetime(2021, 3, 18),
}

dag = DAG('console_script', schedule_interval=None,
          default_args=args)

get_files = BashOperator(
    task_id='get_files',
    bash_command='python3 /opt/DataMining/main.py',
    dag=dag)
