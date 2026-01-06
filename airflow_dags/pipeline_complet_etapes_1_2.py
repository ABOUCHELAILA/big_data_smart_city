"""
DAG Airflow complet pour les Étapes 1 et 2 du pipeline Big Data
Étape 1: Génération des données (Data Collection)
Étape 2: Ingestion des données (Streaming Kafka)
Étape 2: Vérification (Consumer Kafka)
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago


default_args = {
    'owner': 'data_engineer',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Définition du DAG
dag = DAG(
    'pipeline_complet_etapes_1_2',
    default_args=default_args,
    description='Pipeline Big Data complet - Étapes 1, 2 et 3: Génération, Ingestion Kafka, Vérification et Stockage HDFS',
    schedule_interval=None,  # Manuel uniquement pour les tests
    start_date=days_ago(1),
    catchup=False,
    tags=['pipeline', 'etapes-1-2-3', 'kafka', 'hdfs', 'smart-city', 'complet', 'data-lake'],
    doc_md='''
    ## Pipeline Big Data - Étapes 1, 2 et 3
    
    ### Objectif complet
    Valider le fonctionnement complet des trois premières étapes du pipeline Big Data :
    1. **Génération des données** : Simulation de capteurs Smart City
    2. **Ingestion Kafka** : Streaming temps réel des événements
    3. **Vérification** : Consommation et validation des messages
    4. **Stockage HDFS** : Data Lake Raw Zone organisé par date et zone
    
    ### Structure des données
    ```json
    {
      "sensor_id": "string",
      "road_id": "string", 
      "road_type": "autoroute | avenue | rue",
      "zone": "string",
      "vehicle_count": integer,
      "average_speed": float,
      "occupancy_rate": float,
      "event_time": "yyyy-MM-dd HH:mm:ss"
    }
    ```
    
    ### Tâches séquentielles
    - **generation_et_ingestion** : Combine génération et ingestion Kafka
    - **verification_kafka** : Consomme et valide les messages reçus
    - **stockage_hdfs** : Stocke les données brutes dans HDFS Data Lake
    
    ### Validation
    - Messages générés avec structure JSON conforme
    - Envoi réussi vers Kafka (topic: traffic-events)
    - Réception et validation des messages
    - Stockage organisé dans HDFS (/data/raw/traffic)
    - Performance mesurée (1+ événements/seconde)
    - Bout en bout confirmé
    ''',
)

# Tâche unifiée : Génération + Ingestion Kafka
generation_et_ingestion = BashOperator(
    task_id='generation_et_ingestion',
    bash_command='cd /opt/airflow && '
        'echo "=== ÉTAPE 1: Génération des données ===" && '
        'python data_generator/traffic_data_generator.py --sensors 15 --events-per-second 4 --duration 50 && '
        'echo "=== ÉTAPE 2: Ingestion Kafka ===" && '
        'python kafka_producer/kafka_producer_simple.py --bootstrap-servers kafka:29092 --events-per-second 4 --duration 50 && '
        'echo "=== Messages générés et envoyés vers Kafka ==="',
    dag=dag,
    doc_md='''
    ### Étape 1 : Génération des données
    
    Génère 200 événements de trafic réalistes :
    - 15 capteurs simulés
    - 4 événements/seconde pendant 50 secondes
    - Structure JSON obligatoire respectée
    - Zones variées : Centre-ville, Périphérie, Zone industrielle, etc.
    
    ### Étape 2 : Ingestion Kafka
    
    Envoie les événements vers Kafka :
    - Topic : traffic-events
    - 5 partitions pour la parallélisation
    - Partitionnement par zone géographique
    - 200 événements envoyés au total
    - Compression gzip pour optimiser le réseau
    
    ### Résultat
    - Messages générés et stockés temporairement
    - Envoi réussi vers Kafka
    - Prêt pour la consommation
    ''',
)

# Tâche 2 : Vérification Kafka
verification_kafka = BashOperator(
    task_id='verification_kafka',
    bash_command='cd /opt/airflow && '
        'echo "=== ÉTAPE 3: Vérification Kafka ===" && '
        'python kafka_consumer/kafka_consumer_simple.py --bootstrap-servers kafka:29092 --max-messages 50 --timeout 30 && '
        'echo "=== Messages reçus et validés ==="',
    dag=dag,
    doc_md='''
    ### Étape 3 : Vérification de la réception Kafka
    
    Consomme et valide les messages depuis Kafka :
    - 50 messages maximum à recevoir (échantillon des 200 générés)
    - Timeout de 30 secondes
    - Affichage détaillé des messages reçus
    - Validation de la structure JSON
    - Vérification des zones, véhicules, vitesse, heure
    
    ### Résultat
    - Messages reçus depuis Kafka
    - Structure JSON intacte
    - Données validées et affichées
    - Confirmation du pipeline temps réel fonctionnel
    ''',
)

# Tâche 3 : Stockage HDFS
stockage_hdfs = BashOperator(
    task_id='stockage_hdfs',
    bash_command='cd /opt/airflow && '
        'echo "=== ÉTAPE 3: Stockage HDFS - CONSOMMATION COMPLÈTE ===" && '
        'pip install --user requests && '
        'python kafka_consumer/kafka_consumer_hdfs_rest.py --bootstrap-servers kafka:29092 --namenode-host namenode --namenode-port 9870 --batch-size 20 --timeout 30 && '
        'echo "=== TOUS les messages stockés dans HDFS ==="',
    dag=dag,
    doc_md='''
    ### Étape 3 : Stockage des données brutes (Data Lake - Raw Zone)
    
    Consomme TOUS les messages Kafka et les stocke dans HDFS :
    - Utilise l''API REST HDFS (WebHDFS)
    - Crée le répertoire /data/raw/traffic dans HDFS
    - Organise les données par date et zone
    - Stocke les messages en format JSON
    - CONSOMMATION COMPLÈTE : tous les messages du topic
    - Batch size: 20 messages par fichier
    - Timeout: 30 secondes sans nouveau message
    - Installation automatique de requests
    
    ### Structure HDFS
    - /data/raw/traffic/{zone}/{YYYY/MM/DD}/traffic_events_{timestamp}.json
    
    ### Résultat
    - TOUS les messages consommés depuis Kafka
    - Données brutes stockées dans HDFS
    - Organisation par zone et date
    - Vérification du stockage effectué
    ''',
)

# Définition des dépendances : Flux séquentiel
generation_et_ingestion >> verification_kafka >> stockage_hdfs
