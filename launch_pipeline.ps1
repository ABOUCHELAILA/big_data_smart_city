# Lancement automatique du pipeline Big Data Smart City (PowerShell)
Write-Host "🚦 LANCEMENT AUTOMATIQUE DU PIPELINE BIG DATA SMART CITY" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green

# Vérifier que Docker est en cours d'exécution
Write-Host "📋 Vérification des conteneurs Docker..." -ForegroundColor Yellow
$dockerCheck = docker ps | Select-String "airflow-webserver"
if (-not $dockerCheck) {
    Write-Host "❌ Airflow n'est pas en cours d'exécution" -ForegroundColor Red
    Write-Host "🐳 Démarrage de l'infrastructure..." -ForegroundColor Yellow
    docker-compose up -d
    Write-Host "⏳ Attente de 60 secondes pour l'initialisation..." -ForegroundColor Yellow
    Start-Sleep -Seconds 60
}

Write-Host "✅ Infrastructure Docker prête" -ForegroundColor Green

# Lancer le DAG automatiquement via l'API REST Airflow
Write-Host "🚀 Lancement automatique du DAG pipeline_complet_etapes_1_2..." -ForegroundColor Yellow

# Variables
$airflowUrl = "http://localhost:8081/api/v1/dags/pipeline_complet_etapes_1_2/dagRuns"
$username = "airflow"
$password = "airflow"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$jsonDate = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"

# Créer le corps de la requête
$jsonData = @{
    dag_run_id = "manual_run_$timestamp"
    logical_date = $jsonDate
    conf = @{}
} | ConvertTo-Json

# Lancer le DAG
Write-Host "📤 Envoi de la requête à Airflow..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri $airflowUrl -Method POST -Body $jsonData -ContentType "application/json" -Headers @{Accept = "application/json"} -Credential (New-Object System.Management.Automation.PSCredential($username, (ConvertTo-SecureString $password -AsPlainText -Force)))
    
    if ($response.dag_run_id) {
        $dagRunId = $response.dag_run_id
        Write-Host "✅ DAG lancé avec succès !" -ForegroundColor Green
        Write-Host "🆔 Run ID: $dagRunId" -ForegroundColor Cyan
        Write-Host "🌐 Suivez l'exécution sur: http://localhost:8081" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "📊 Commande pour vérifier le statut:" -ForegroundColor Yellow
        Write-Host "curl -u airflow:airflow http://localhost:8081/api/v1/dags/pipeline_complet_etapes_1_2/dagRuns/$dagRunId" -ForegroundColor Gray
        Write-Host ""
        Write-Host "🎯 Pipeline en cours d'exécution..." -ForegroundColor Green
        Write-Host "📂 Les données seront stockées dans HDFS: /data/raw/traffic/" -ForegroundColor Cyan
        Write-Host "🔍 Surveillez les logs dans Airflow UI: http://localhost:8081" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "⏱️  Temps estimé: 2-3 minutes pour les 3 tâches" -ForegroundColor Yellow
    } else {
        Write-Host "❌ Erreur lors du lancement du DAG" -ForegroundColor Red
        Write-Host "Réponse: $response" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Erreur de connexion à Airflow: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Vérifiez que Airflow est accessible sur http://localhost:8081" -ForegroundColor Yellow
    exit 1
}

Write-Host "==================================================" -ForegroundColor Green
