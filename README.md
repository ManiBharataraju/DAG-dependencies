# DAG-dependencies

DAG-dependencies was created to understand the dependencies between the dags in Airflow. 

It follows the below design

1) The dependencies are identified with dags having TriggerDagRunOperator or ExternalTaskSensor
2) The dependency details are loaded into a table called dag_dependencies. As part of the project, this table was created in a postgres database but it can be any database that is supported by python. 
3) The dags properties like the schedule, tags etc. are stored in the dag_properties table.
4) The dags status running, failed etc is stored in the dag_states table.


# How the tables are loaded
1) These tables are loaded thru the two dags. They access the airflow metadata tables like the DagRun, TaskInstance etc. to fetch the data and transformed per the table needs.
2) The status of the dags is updated every 5 mins in the table while the dependencies are updated on demand by manual trigger.


#Table Structures

CREATE TABLE 
    dag_dependencies 
    ( 
        dag_name       CHARACTER VARYING(128), 
        downstream_dep CHARACTER VARYING(128), 
        OPERATOR       CHARACTER VARYING(128) 
    );
 
 CREATE TABLE 
    dag_properties
    ( 
        dag_name  CHARACTER VARYING(128), 
        sla_tag   CHARACTER(1), 
        SCHEDULE  CHARACTER VARYING(64), 
        is_paused BOOLEAN 
    );
    
    
  CREATE TABLE 
    dag_states
    ( 
        dag_name       CHARACTER VARYING(150), 
        execution_date CHARACTER VARYING(50), 
        start_time     CHARACTER VARYING(50), 
        end_time       CHARACTER VARYING(50), 
        state          CHARACTER VARYING(10), 
        recency_flag   CHARACTER(1), 
        run_time       CHARACTER VARYING(35) 
    );
    
    ![image](https://user-images.githubusercontent.com/9946408/121780244-20886800-cbbd-11eb-87bc-0b8704d4f536.png)
