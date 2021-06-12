# DAG-dependencies

DAG-dependencies is a project created to understand the dependencies between the dags in Airflow. 

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


Separate UI for linked and non linked dags
<img> ![image](https://user-images.githubusercontent.com/9946408/121780811-9b528280-cbbf-11eb-9b0b-cbfe3da8499d.png) </img>
hide/show legend switch between darkmode and light mode
<img> ![image](https://user-images.githubusercontent.com/9946408/121780840-c5a44000-cbbf-11eb-9632-91a533e06b26.png) </img>

click on any node to check history/dependency
<img> ![image](https://user-images.githubusercontent.com/9946408/121780863-db196a00-cbbf-11eb-9ac2-599145766f9c.png) </img>

Click on history to see the data about dag runs
<img> ![image](https://user-images.githubusercontent.com/9946408/121780872-e8365900-cbbf-11eb-8fde-037aed2c6f3d.png) </img>

Click on dependencies to see the edges highlighted
<img> ![image](https://user-images.githubusercontent.com/9946408/121780899-09974500-cbc0-11eb-9e1d-fb9af370e561.png) </img>

tooltip to understand dependencies

<img> ![image](https://user-images.githubusercontent.com/9946408/121781013-84606000-cbc0-11eb-9e10-ecd936e31e86.png)</img>
<img> ![image](https://user-images.githubusercontent.com/9946408/121781040-a9ed6980-cbc0-11eb-9a5f-356136b9d47e.png) </img>
 



 



