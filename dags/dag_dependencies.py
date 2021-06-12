'''

This DAG pulls dependencies of each DAG from the dag bag and inserts them in to table dag_dependencies.
It also loads the SLA tags and schedules for each DAG and inserts into dag_properties table

'''

import logging
from datetime import datetime
from airflow import DAG
from airflow.models import Variable, DagRun, DagBag, DagTag
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.dagrun_operator import TriggerDagRunOperator
from airflow.sensors.external_task_sensor import ExternalTaskSensor
from airflow.utils.db import provide_session

from airflow.providers.postgres.hooks.postgres import DWPostgresHook
from airflow.operators.python import PythonOperator


@provide_session
def get_dag_info(session = None, **kwargs):
    # used for storing dag, downstream dep, operator (ETS or TDR)
    dag_dependencies = {}
    # used to keep running list of all dags in dag bag
    all_dags = set()
    # used to determine linked/nonlinked dags
    linked_dags = set()

    dag_properties_rows = []
    for dag in DagBag().dags.values():
        if dag.parent_dag is None:
            all_dags.add(dag.dag_id)
            # query below selects SLA tag for the dag that is currently being looped
            tag_info = session.query(DagTag.name).filter(DagTag.dag_id == dag.dag_id).all()
            SLA_tag = 'N'
            # assigns SLA tags
            if tag_info:
                tags = [tag_info[0] for tag in tag_info]
                SLA_tag = 'Y' if 'SLA'in tags else 'N'

            # build query to insert into dag_properties table below
            dag_properties_rows.append(f"SELECT '{dag.dag_id}' as dag_name, '{SLA_tag}' as SLA_tag, '{str(dag.schedule_interval)}' as schedule")

            # for loop below builds dag_dependencies which stores dependency info to later be queried
            for task in dag.tasks:
                if isinstance(task, ExternalTaskSensor):
                    linked_dags.add(dag.dag_id)
                    linked_dags.add(task.external_dag_id)
                    if dag.dag_id != task.external_dag_id:
                        # 'E' means external task sensor dependency
                        if (task.external_dag_id, 'E') not in dag_dependencies.keys():
                                dag_dependencies[(task.external_dag_id, 'E')] = [dag.dag_id]
                        else:
                            if dag.dag_id not in dag_dependencies[(task.external_dag_id, 'E')]:
                                dag_dependencies[(task.external_dag_id, 'E')].append(dag.dag_id)
        
                if isinstance(task, TriggerDagRunOperator):
                    linked_dags.add(dag.dag_id)
                    linked_dags.add(task.trigger_dag_id)
                    # 'T' means trigger dag run operator dependency
                    if (dag.dag_id, 'T') not in dag_dependencies.keys():
                        dag_dependencies[(dag.dag_id, 'T')] = [task.trigger_dag_id]
                    else:
                        if task.trigger_dag_id not in dag_dependencies[(dag.dag_id, 'T')]:
                            dag_dependencies[(dag.dag_id, 'T')].append(task.trigger_dag_id)

    # set operation to generate list of non linked dags
    nonlinked_dags = all_dags - linked_dags

    # variable below will be used to join select queries
    dag_dependency_rows = []                    
    # loops below build select queries which will later be used in insert
    for key in dag_dependencies:
        parent_dag , operator = key
        for dependent_dag in dag_dependencies[key]:
            dag_dependency_rows.append(f"SELECT '{parent_dag}' as dag_name, '{dependent_dag}' as downstream_dep, '{operator}' as operator")

    for non_linked_dag in nonlinked_dags:
        dag_dependency_rows.append(f"SELECT '{non_linked_dag}' as dag_name, NULL as downstream_dep, NULL as operator")

    #logging.info(f"{rows}")
    
    dag_dependency_rows = ' union all '.join(dag_dependency_rows)
    dag_properties_rows = ' union all '.join(dag_properties_rows)

    # dag_dependencies table has 'D' values for column operator which are used for dummy nodes when gru visualizes time deps

    schema = '<your schema name>'
    sql= f"""BEGIN; 
             DELETE from {schema}.dag_dependencies where operator<>'D' or operator is null; INSERT into {schema}.dag_dependencies {dag_dependency_rows};
             TRUNCATE table {schema}.dag_properties; INSERT INTO {schema}.dag_properties {dag_properties_rows}; 
             COMMIT;"""

    conn = DWPostgresHook(postgres_conn_id='<your db conn id>')
    results = conn.run(sql)

args = {
    'owner': 'mani',
}

with DAG(
    dag_id='dag_dependencies',
    default_args=args,
    start_date=datetime(2021, 6, 9),
    schedule_interval="@once",
) as dag:

    get_dag_info_task = PythonOperator(
        task_id='get_dag_info_task',
        python_callable=get_dag_info,
        provide_context=True
    )

    get_dag_info_task