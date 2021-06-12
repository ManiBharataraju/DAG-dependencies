'''

This DAG pulls dag statuses such as running, completed, failed and inserts them into the DB
table dag_status. It does this for the most recent five DAG runs, and the data from the DB is used to render
on UI

'''
import logging
from datetime import datetime
from sqlalchemy import func
from airflow import DAG
from airflow.models import Variable, DagRun, DagBag, DagTag, TaskInstance, DagModel
from airflow.utils.db import provide_session
from airflow.utils.state import State

from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.operators.python import PythonOperator


#RECENCY_FLAG will indicate in last 5 dag run table which run is most recent, 'L' meanest latest
RECENCY_FLAG_LATEST = 'L'
RECENCY_FLAG_OLD = 'O'

@provide_session
def get_dag_status(session=None, **kwargs):

    schema = '<your schema name>'
    sql = f"""
            SELECT 
                dag_name 
            FROM 
                {schema}.dag_dependencies 
            WHERE 
                OPERATOR <> 'D' 
            OR  OPERATOR IS NULL 
            UNION  
            SELECT 
                downstream_dep 
            FROM 
                {schema}.dag_dependencies 
            WHERE 
                downstream_dep IS NOT NULL;"""

    conn = PostgresHook(postgres_conn_id='<your conn id>')
    dag_list = conn.get_records(sql)
    list_select_queries_state = []
    dag_current_active_status = []
    for dag in dag_list:
        dag_id = dag[0]
        # statement below generates dag_info object which containts info of last 5 dag runs
        DR = DagRun
        TI = TaskInstance
        # query below generates tuple of last 5 dag runs
        dag_info = session.query(DR.dag_id, DR.execution_date, func.min(TI.start_date), DR.end_date, DR.state).filter(
            DR.dag_id == dag[0], DR.dag_id == TI.dag_id, DR.execution_date == TI.execution_date).group_by(
            DR.dag_id, DR.execution_date, DR.end_date, DR.state).order_by(DR.execution_date.desc()).limit(5)
        # get current time and get rid of microseconds, use this time to calculate runtime of running dags
        now = datetime.utcnow()
        now = now.replace(microsecond=0)
        # recency_flag below determines which state in last 5 dag runs is most recent and will be populated in modal
        recency_flag = RECENCY_FLAG_LATEST
        for info in dag_info.all():
            # destructure info tuple below
            dag_name, exec_date_w_ms, start_date_w_ms, end_date_w_ms, state = info
            exec_date = exec_date_w_ms.replace(tzinfo=None, microsecond=0)
            # logic below to generate runtime and get rid of milliseconds and UTC offset and
            # determines if times are invalid in case when airflow task start is not valid
            if start_date_w_ms != None:
                start_date = start_date_w_ms.replace(tzinfo=None, microsecond=0)
            else:
                start_date = 'invalid'
            if end_date_w_ms != None:
                end_date = end_date_w_ms.replace(tzinfo=None, microsecond=0)
            else:
                end_date = 'invalid'
            if end_date != 'invalid' and start_date != 'invalid':
                run_time = end_date - start_date
            elif state == State.RUNNING and start_date != 'invalid':
                run_time = now - start_date
                end_date = ' '
            else:
                run_time = 'invalid'
            # build select statement below using elements from dag_info
            list_select_queries_state.append(f"""
                SELECT '{dag_name}' as dag_name,
                       '{exec_date}' as execution_date,
                       '{start_date}' as start_date,
                       '{end_date}' as end_date,
                       '{state}' as state,
                       '{recency_flag}' as recency_flag,
                       '{run_time}' as run_time
                            """)
            recency_flag = RECENCY_FLAG_OLD

        #Check if dag is turned off
        if kwargs['execution_date'].hour in [0,12] and kwargs['execution_date'].minute == 0:
            
            is_paused = session.query(DagModel.is_paused).filter(DagModel.dag_id == dag_id).all()[0][0]
            dag_current_active_status.append(f"select '{dag_id}' as dag_name, {is_paused} as status")  

    # join select statements below with union all statement so it can be later inserted
    unionAllStringState = ' union all '.join(list_select_queries_state)
    sql= f"BEGIN; TRUNCATE table {schema}.dag_states; INSERT into {schema}.dag_states {unionAllStringState}; COMMIT;"
    conn.run(sql)

    #Update the dag status in the dag_properties table
    if kwargs['execution_date'].hour in [0,12] and kwargs['execution_date'].minute == 0:

        dag_current_active_status = ' union all '.join(dag_current_active_status)
        sql = f"""  BEGIN;
                    update {schema}.dag_properties d set is_paused = ds.status  from ({dag_current_active_status}) ds where d.dag_name=ds.dag_name;
                    COMMIT;"""
        
        conn.run(sql)




args = {
    'owner': 'mani',
}

with DAG(
    dag_id='dag_dependencies',
    default_args=args,
    start_date=datetime(2021, 6, 9),
    schedule_interval="0/5 * * * *",
) as dag:

    get_dag_status_task = PythonOperator(
        task_id='get_dag_status_task',
        python_callable=get_dag_status,
        provide_context=True
    )
    get_dag_status_task 
