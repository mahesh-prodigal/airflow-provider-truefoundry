from airflow import DAG
from datetime import datetime, timedelta
from truefoundry_provider.operators.job_run_now import TrueFoundryJobRunNowOperator

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'sample_operator_dag',
    default_args=default_args,
    description='A DAG with a sample operator',
    schedule_interval=None,
    params={
        "application_fqn": '',
        "command": '',
        'parameters': '',
        'truefoundry_conn_id': ''
    }
)

sample_task = TrueFoundryJobRunNowOperator(
    task_id='sample_task',
    application_fqn="{{ params.application_fqn or None }}",
    truefoundry_conn_id="{{ params.truefoundry_conn_id or None }}",
    command="{{ params.command if  params.command }}",
    parameters="{{ params.parameters if  params.parameters}}",
    dag=dag,
)