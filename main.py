from flask import Flask, render_template
import json
import psycopg2

import os
import configparser

conn = None
cur = None

def get_conf_val():
    config = configparser.RawConfigParser()

    parent_dir=os.path.dirname(os.path.abspath(__file__))

    conf_path=os.path.join(parent_dir,'config/')

    config.read(conf_path+'dbconfig.conf')

    db_conf={k:v for (k,v) in config.items('main')}

    return db_conf


def get_db_conn():
    '''
    method to create db connection to extract data
    '''

    global conn
    db_conf=get_conf_val()

    if conn is None:
        conn = psycopg2.connect(database=db_conf['database'], user=db_conf['user'],
                                password=db_conf['password'], host=db_conf['host'], port=db_conf['port'])
        print("Database opened successfully")
        cur = conn.cursor()
    else:
        try:
            cur = conn.cursor()
            cur.execute('select 1;')
            out = cur.fetchall()
        except:
            conn = psycopg2.connect(database=db_conf['database'], user=db_conf['user'],
                                password=db_conf['password'], host=db_conf['host'], port=db_conf['port'])
            print("Database opened successfully")
            conn.set_session(readonly=True, autocommit=True)
            cur = conn.cursor()

    return cur


def get_dag_state(cur):
    '''
    Method to fetch the current state and status history of dags
    '''

    # get the most recent state(Running/Success/Failed) of dags
    cur.execute("Select dag_name,state from dag_states where recency_flag='L'")
    dag_status_from_db = cur.fetchall()

    dag_status = {}
    for dag in dag_status_from_db:
        dag_name = dag[0]
        current_state = dag[1]
        dag_status[dag_name] = current_state

    # get the history of dags with start time, end time and status
    cur.execute(
        """SELECT dag_name, execution_date, start_time, end_time, state, run_time 
                  FROM dag_states  
           order by dag_name,recency_flag, execution_date desc""")
    dag_status_history_from_db = cur.fetchall()

    dag_status_history = {}
    for dag_info in dag_status_history_from_db:

        dag_name = dag_info[0]
        execution_date = dag_info[1]
        start_time = dag_info[2]
        end_time = dag_info[3] if dag_info[3] is not None else ''
        state = dag_info[4]
        run_time = dag_info[5]

        if dag_name not in dag_status_history.keys():
            dag_status_history[dag_name] = [[execution_date, start_time, end_time, state, run_time]]
        else:
            dag_status_history[dag_name].append([execution_date, start_time, end_time, state, run_time])

    return [dag_status, dag_status_history]

def get_linked():
    '''
    method to fetch the the data of linked dags.
    '''

    cur = get_db_conn()

    # get the linked dags

    cur.execute(
        """SELECT dag_name,downstream_dep,operator 
                FROM dag_dependencies
           WHERE downstream_dep is not null 
           order by dag_name,downstream_dep asc;""")
    all_nodes_with_successor_from_db = cur.fetchall()


    # Identify all the unique dags
    cur.execute("""Select a.dag_name,coalesce(b.sla_tag,'N'),b.schedule,coalesce(sla_name,'None') as sla_name,is_paused::varchar(10) from (Select dag_name from dag_dependencies where downstream_dep is not null 
                    union select downstream_dep from dag_dependencies where downstream_dep is not null) a
                    left outer join
                    (select dag_name,sla_tag,schedule,is_paused from dag_properties group by 1,2,3,4)b
                    on a.dag_name=b.dag_name
                    left outer join
                    (select dag_id, STRING_AGG(sla_name||'('||sla_deadline||' CT)' ,',') as sla_name from cntl_sla group by dag_id) c
                    on b.dag_name=c.dag_id
                    and b.sla_tag='Y'
                    order by 1;""")
    all_nodes = cur.fetchall()

    dag_state = get_dag_state(cur)
    dag_status = dag_state[0]
    dag_status_history = dag_state[1]
    cur.close()

    return [all_nodes_with_successor_from_db, all_nodes, dag_status, dag_status_history]


def get_nonlinked():
    '''
    Method to fetch the data of nonlinked dags
    '''
    cur = get_db_conn()

    cur.execute("""select a.dag_name,b.is_paused from (select dag_name from dag_dependencies where downstream_dep is null order by dag_name)a
                left outer join
                (select dag_name,sla_tag,schedule,is_paused::varchar(10) from dag_properties group by 1,2,3,4)b
                on a.dag_name=b.dag_name;
        """)
    nonlinked_nodes_from_db = cur.fetchall()

    nonlinked_nodes = [node[0] for node in nonlinked_nodes_from_db]
    dag_active_status={}
    for dag_name,is_paused in nonlinked_nodes_from_db:
        dag_active_status[dag_name]=is_paused

    # get the current state and history of dag
    dag_state = get_dag_state(cur)
    dag_status = dag_state[0]
    dag_status_history = dag_state[1]
    cur.close()

    return [nonlinked_nodes, dag_status, dag_status_history,dag_active_status]


app = Flask(__name__)


@app.route("/")
def index():
    rows = get_linked()
    return render_template('index.html', all_nodes_with_successor=rows[0], all_nodes=rows[1], status=rows[2],dag_status_history=rows[3]
                           , env=<your airflow url>)


@app.route('/nonlinked')
def non_linked():
    rows = get_nonlinked()
    return render_template('nonlinked.html', all_nodes=rows[0], status=rows[1], dag_status_history=rows[2],dag_active_status=rows[3]
                           ,env=<your airflow url>)


if __name__ == "__main__":
    app.run(host='localhost', port=3000, debug=False)


