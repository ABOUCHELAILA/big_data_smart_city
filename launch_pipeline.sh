#!/bin/bash

# Lancement automatique du pipeline Big Data Smart City
echo "🚦 LANCEMENT AUTOMATIQUE DU PIPELINE BIG DATA SMART CITY"
echo "=================================================="

# Vérifier que Docker est en cours d'exécution
echo "📋 Vérification des conteneurs Docker..."
if ! docker ps | grep -q "airflow-webserver"; then
    echo "❌ Airflow n'est pas en cours d'exécution"
    echo "🐳 Démarrage de l'infrastructure..."
    docker-compose up -d
    echo "⏳ Attente de 60 secondes pour l'initialisation..."
    sleep 60
fi

echo "✅ Infrastructure Docker prête"

# Lancer le DAG automatiquement via l'API REST Airflow
echo "🚀 Lancement automatique du DAG pipeline_complet_etapes_1_2..."

# Variables
AIRFLOW_URL="http://localhost:8081/api/v1/dags/pipeline_complet_etapes_1_2/dagRuns"
USERNAME="airflow"
PASSWORD="airflow"

# Créer le corps de la requête
JSON_DATA='{
    "dag_run_id": "manual_run_'$(date +%Y%m%d_%H%M%S)'",
    "logical_date": "'$(date +%Y-%m-%dT%H:%M:%SZ)'",
    "conf": {}
}'

# Lancer le DAG
echo "📤 Envoi de la requête à Airflow..."
RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -H "Accept: application/json" \
    -u "$USERNAME:$PASSWORD" \
    -d "$JSON_DATA" \
    "$AIRFLOW_URL")

# Vérifier la réponse
if echo "$RESPONSE" | grep -q '"dag_run_id"'; then
    DAG_RUN_ID=$(echo "$RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin)['dag_run_id'])")
    echo "✅ DAG lancé avec succès !"
    echo "🆔 Run ID: $DAG_RUN_ID"
    echo "🌐 Suivez l'exécution sur: http://localhost:8081"
    echo ""
    echo "📊 Commande pour vérifier le statut:"
    echo "curl -u airflow:airflow http://localhost:8081/api/v1/dags/pipeline_complet_etapes_1_2/dagRuns/$DAG_RUN_ID"
else
    echo "❌ Erreur lors du lancement du DAG"
    echo "Réponse: $RESPONSE"
    exit 1
fi

echo ""
echo "🎯 Pipeline en cours d'exécution..."
echo "📂 Les données seront stockées dans HDFS: /data/raw/traffic/"
echo "🔍 Surveillez les logs dans Airflow UI: http://localhost:8081"
echo ""
echo "⏱️  Temps estimé: 2-3 minutes pour les 3 tâches"
echo "=================================================="
