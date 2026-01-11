from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago

default_args = {
    'owner': 'data_engineer',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'pipeline_complet_etapes_1_7',
    default_args=default_args,
    description='Pipeline Smart City End-to-End',
    schedule_interval=None,
    start_date=days_ago(1),
    catchup=False,
    tags=['smart-city', 'big-data'],
)

# Étape 1 & 2: Génération + Ingestion Kafka
generation_et_ingestion = BashOperator(
    task_id='etape_1_2_generation_ingestion',
    bash_command='cd /opt/airflow && python3 data_generator/traffic_data_generator.py --sensors 20 --events-per-second 5 --duration 60 && python3 kafka_producer/kafka_producer_simple.py --bootstrap-servers kafka:29092 --events-per-second 5 --duration 60',
    dag=dag,
)

# Étape 2 (suite): Vérification Kafka
verification_kafka = BashOperator(
    task_id='etape_2_verification_kafka',
    bash_command='cd /opt/airflow && python3 kafka_consumer/kafka_consumer_simple.py --bootstrap-servers kafka:29092 --max-messages 50 --timeout 30',
    dag=dag,
)

# Étape 3: Stockage HDFS Raw Zone
stockage_hdfs_raw = BashOperator(
    task_id='etape_3_stockage_hdfs_raw',
    bash_command='cd /opt/airflow && python3 kafka_consumer/kafka_consumer_hdfs_rest.py --bootstrap-servers kafka:29092 --namenode-host namenode --namenode-port 9870 --batch-size 30 --timeout 40',
    dag=dag,
)

# Étape 4: Traitement Spark
traitement_spark = BashOperator(
    task_id='etape_4_traitement_spark',
    bash_command='cd /opt/airflow && python3 spark_processing/traffic_processor.py --hdfs-namenode hdfs://namenode:9000 --raw-path /data/raw/traffic --output-path /data/processed/traffic',
    dag=dag,
)

# Étape 5: Conversion Parquet (Analytics Zone)
conversion_parquet = BashOperator(
    task_id='etape_5_analytics_parquet',
    bash_command='cd /opt/airflow && python3 analytics/parquet_converter.py --hdfs-namenode hdfs://namenode:9000 --processed-path /data/processed/traffic --analytics-path /data/analytics/traffic',
    dag=dag,
)

# Étape 6: Validation Qualité
validation_qualite = BashOperator(
    task_id='etape_6_validation_qualite',
    bash_command='cd /opt/airflow && python3 scripts/validate_data_quality.py --hdfs-namenode http://namenode:9870',
    dag=dag,
)

# Étape 7: Export final
export_metriques = BashOperator(
    task_id='etape_7_export_metriques',
    bash_command='echo "✓ Pipeline terminé. Données disponibles dans Grafana."',
    dag=dag,
)

# Ordre d'exécution
generation_et_ingestion >> verification_kafka >> stockage_hdfs_raw >> traitement_spark >> conversion_parquet >> validation_qualite >> export_metriques