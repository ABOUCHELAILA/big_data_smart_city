# 🚦 Pipeline Big Data Smart City - Analyse du Trafic Urbain

## 📋 Vue d'ensemble

Ce projet implémente un pipeline Big Data End-to-End pour l'analyse du trafic urbain et de la mobilité intelligente dans le cadre des Smart Cities.

### 🎯 Objectifs

- **Collecte** : Simuler des capteurs de trafic urbain en temps réel
- **Ingestion** : Streaming Apache Kafka pour données IoT
- **Stockage** : Data Lake HDFS avec organisation par zone/date
- **Orchestration** : Apache Airflow pour automatisation

### 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Générateur   │───▶│     Kafka       │───▶│      HDFS      │───▶│   Airflow DAG   │
│   Données       │    │   (Streaming)   │    │   (Data Lake)   │    │  (Orchestration)│
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## 🚀 Prérequis

### Logiciels requis
- **Docker Desktop** (Windows/Mac) ou **Docker Engine** (Linux)
- **Docker Compose**
- **Git** (optionnel, pour cloner le projet)

### Configuration système recommandée
- **RAM** : 8GB minimum (16GB recommandé)
- **CPU** : 4 cores minimum
- **Disque** : 10GB d'espace libre

---

## 📦 Installation et Démarrage

### 1. Cloner le projet
```bash
git clone <repository-url>
cd laila_big_data
```

### 2. Démarrer l'infrastructure
```bash
# Démarrer tous les services
docker-compose up -d

# Vérifier que tous les conteneurs sont actifs
docker ps
```

### 3. Attendre l'initialisation (2-3 minutes)
Les services suivants démarrent :
- **Zookeeper** (port 2181)
- **Kafka** (port 29092)
- **Kafka UI** (port 8080)
- **HDFS NameNode** (port 9000, 9870)
- **HDFS DataNode** (port 9864, 9866)
- **PostgreSQL** (port 5432)
- **Airflow Webserver** (port 8081)
- **Airflow Scheduler**

### 4. Accéder aux interfaces web
- **Airflow UI** : http://localhost:8081 (airflow/airflow)
- **Kafka UI** : http://localhost:8080
- **HDFS NameNode UI** : http://localhost:9870

---

## 🚀 Lancement Automatique

### Option 3 : Lancement terminal (Automatique)

#### Linux/Mac
```bash
# Rendre le script exécutable
chmod +x launch_pipeline.sh

# Lancer le pipeline automatiquement
./launch_pipeline.sh
```

#### Windows PowerShell
```powershell
# Lancer le pipeline automatiquement
.\launch_pipeline.ps1
```

#### Que fait le lancement automatique ?
1. **Vérifie Docker** : Démarre l'infrastructure si nécessaire
2. **Attend l'initialisation** : 60 secondes pour tous les services
3. **Lance le DAG** : Via API REST Airflow
4. **Retourne l'ID** : Pour suivre l'exécution
5. **Surveillance** : Liens vers Airflow UI et logs

#### Avantages du lancement automatique
- **Pas d'interface web** : Tout depuis le terminal
- **Scriptable** : Intégrable dans d'autres automatisations
- **Rapide** : Un seule commande pour tout lancer
- **Monitoring** : ID d'exécution pour suivi

---

## 🎯 Utilisation du Pipeline

### Option 1 : Via Airflow UI (Recommandé)

1. **Ouvrir Airflow** : http://localhost:8081
2. **Se connecter** : airflow / airflow
3. **Activer le DAG** : `pipeline_complet_etapes_1_2`
4. **Déclencher manuellement** : bouton "Trigger DAG"
5. **Surveiller l'exécution** : 3 tâches séquentielles

### Option 2 : Lancement manuel (Tests)

#### Génération de données
```bash
docker exec airflow-webserver bash -c "
cd /opt/airflow && 
python data_generator/traffic_data_generator.py --sensors 10 --events-per-second 2 --duration 30
"
```

#### Ingestion Kafka
```bash
docker exec airflow-webserver bash -c "
cd /opt/airflow && 
python kafka_producer/kafka_producer_simple.py --bootstrap-servers kafka:29092 --events-per-second 2 --duration 30
"
```

#### Vérification Kafka
```bash
docker exec airflow-webserver bash -c "
cd /opt/airflow && 
python kafka_consumer/kafka_consumer_simple.py --bootstrap-servers kafka:29092 --max-messages 10 --timeout 20
"
```

#### Stockage HDFS
```bash
docker exec airflow-webserver bash -c "
cd /opt/airflow && 
python kafka_consumer/kafka_consumer_hdfs_rest.py --bootstrap-servers kafka:29092 --namenode-host namenode --namenode-port 9870 --batch-size 20 --timeout 30
"
```

---

## 📊 Structure des Données

### Format JSON des événements
```json
{
  "sensor_id": "SENSOR_960",
  "road_id": "ROAD_428", 
  "road_type": "avenue",
  "zone": "Zone commerciale",
  "vehicle_count": 8,
  "average_speed": 78.4,
  "occupancy_rate": 0.376,
  "event_time": "2026-01-06 13:48:41"
}
```

### Organisation HDFS
```
/data/raw/traffic/
├── Zone commerciale/
│   └── 2026/01/06/
│       ├── traffic_events_20260106_155700.json
│       └── traffic_events_20260106_155701.json
├── Zone industrielle/
│   └── 2026/01/06/
│       └── traffic_events_20260106_155701.json
└── Quartier residentiel/
    └── 2026/01/06/
        └── traffic_events_20260106_142628.json
```

---

## 🔧 Configuration

### Paramètres du générateur
- `--sensors` : Nombre de capteurs (défaut: 10)
- `--events-per-second` : Fréquence de génération (défaut: 2)
- `--duration` : Durée en secondes (défaut: 30)

### Paramètres Kafka
- `--bootstrap-servers` : Serveurs Kafka (défaut: kafka:29092)
- `--max-messages` : Messages maximum à consommer
- `--timeout` : Timeout en secondes

### Paramètres HDFS
- `--namenode-host` : HDFS NameNode (défaut: namenode)
- `--namenode-port` : Port NameNode (défaut: 9870)
- `--batch-size` : Taille des batchs (défaut: 20)

---

## ⚠️ Conflits de Dépendances Potentiels

### 🐍 Python - Versions compatibles
Le projet est optimisé pour **Python 3.8+** avec les dépendances suivantes :

```txt
kafka-python==2.0.2      # Compatible Python 3.8+
hdfs3==0.3.1           # Compatible Python 3.8+
python-dateutil==2.8.2    # Compatible Python 3.7+
pytz==2023.3             # Compatible Python 3.6+
```

### 🚨 Conflits connus et solutions

#### 1. **Python 3.9+ et hdfs3**
```bash
# Problème : hdfs3==0.3.1 incompatible avec Python 3.9+
# Solution : Utiliser notre version REST (déjà implémentée)
# Le projet utilise kafka_consumer_hdfs_rest.py qui ne dépend pas de hdfs3
```

#### 2. **Conflit de ports système**
```bash
# Ports utilisés par le projet :
8080  # Kafka UI
8081  # Airflow Webserver  
9000  # HDFS NameNode
9870  # HDFS NameNode Web UI
5432  # PostgreSQL

# Vérifier les ports occupés :
netstat -an | grep :8081
netstat -an | grep :8080

# Solution si conflit : Modifier docker-compose.yml
ports:
  - "8082:8081"  # Changer Airflow vers 8082
```

#### 3. **Docker Desktop vs Docker Engine**
```bash
# Windows : Docker Desktop requis
# Linux : Docker Engine + Docker Compose
# macOS : Docker Desktop recommandé

# Vérifier l'installation :
docker --version
docker-compose --version
```

#### 4. **Ressources système insuffisantes**
```bash
# Symptômes : Conteneurs qui redémarrent
# Solution : Augmenter les ressources Docker Desktop
# RAM : 8GB minimum (16GB recommandé)
# CPU : 4 cores minimum
```

#### 5. **Conflits de dépendances locales**
```bash
# Si vous avez déjà Kafka/Hadoop installés localement
# Problème : Ports et services en conflit
# Solution : Arrêter les services locaux ou utiliser différents ports

# Arrêter Kafka local :
systemctl stop kafka-server
systemctl stop zookeeper

# Arrêter Hadoop local :
stop-dfs.sh
stop-yarn.sh
```

### 🔧 Solutions de contournement

#### Option 1 : Utiliser uniquement Docker (Recommandé)
```bash
# Aucune installation locale requise
# Tout est dans les conteneurs Docker
# Pas de conflits de dépendances Python
```

#### Option 2 : Environnement virtuel
```bash
# Créer un environnement isolé
python3.8 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

#### Option 3 : Modification des ports
```yaml
# Dans docker-compose.yml
services:
  airflow-webserver:
    ports:
      - "8082:8081"  # Éviter le conflit
```

### ✅ Vérification avant lancement
```bash
# 1. Vérifier Docker
docker --version
docker-compose --version

# 2. Vérifier les ports
netstat -an | grep -E ":(8080|8081|9000|5432)"

# 3. Vérifier la RAM disponible
# Windows/Mac : Vérifier Docker Desktop settings
# Linux : free -h

# 4. Lancer le projet
docker-compose up -d
```

---

## 🛠️ Dépannage

### Problèmes courants

#### Port déjà utilisé
```bash
# Vérifier les ports utilisés
netstat -an | grep :8081
netstat -an | grep :8080

# Tuer les processus si nécessaire
sudo kill -9 <PID>
```

#### Conteneurs ne démarrent pas
```bash
# Vérifier les logs
docker-compose logs namenode
docker-compose logs kafka
docker-compose logs airflow-webserver

# Redémarrer les services
docker-compose down
docker-compose up -d
```

#### Messages non reçus dans HDFS
```bash
# Vérifier le topic Kafka
docker exec kafka bash -c "kafka-topics --bootstrap-server localhost:29092 --list"

# Vérifier les messages dans le topic
docker exec kafka bash -c "kafka-console-consumer --bootstrap-server localhost:29092 --topic traffic-events --from-beginning --max-messages 5"

# Vérifier HDFS
docker exec namenode bash -c "hdfs dfs -ls -R /data/raw/traffic"
```

#### Airflow DAG n'apparaît pas
```bash
# Rafraîchir les DAGs Airflow
docker exec airflow-webserver bash -c "airflow dags report"

# Redémarrer Airflow
docker-compose restart airflow-webserver airflow-scheduler
```

---

## 📁 Structure du Projet

```
laila_big_data/
├── docker-compose.yml              # Infrastructure Docker
├── requirements.txt               # Dépendances Python
├── airflow_dags/
│   └── pipeline_complet_etapes_1_2.py  # DAG principal
├── data_generator/
│   └── traffic_data_generator.py   # Générateur de données
├── kafka_producer/
│   └── kafka_producer_simple.py   # Producer Kafka
├── kafka_consumer/
│   ├── kafka_consumer_simple.py    # Consumer validation
│   └── kafka_consumer_hdfs_rest.py # Consumer HDFS
├── analytics/                    # Préparé pour analytics futures
├── config/                      # Fichiers de configuration
├── data/                        # Données locales de test
├── logs/                        # Logs des applications
└── scripts/                     # Scripts utilitaires
```

---

## 🚀 Personnalisation

### Ajouter de nouvelles zones
Modifier `data_generator/traffic_data_generator.py` :
```python
ZONES = [
    "Centre-ville",
    "Périphérie", 
    "Zone commerciale",
    "Zone industrielle",
    "Quartier residentiel",
    # Ajouter vos zones ici
]
```

### Modifier la fréquence de génération
Dans le DAG `pipeline_complet_etapes_1_2.py` :
```python
'python data_generator/traffic_data_generator.py --sensors 15 --events-per-second 4 --duration 50'
```

### Changer la taille des batchs HDFS
```python
'python kafka_consumer/kafka_consumer_hdfs_rest.py --batch-size 50'
```

---

## 📈 Monitoring

### Métriques disponibles
- **Kafka UI** : Messages par seconde, lag des consumers
- **Airflow UI** : Durée des tâches, historique d'exécution
- **HDFS UI** : Espace disque utilisé, nombre de fichiers

### Logs
```bash
# Logs Airflow
docker logs airflow-webserver -f
docker logs airflow-scheduler -f

# Logs Kafka
docker logs kafka -f

# Logs HDFS
docker logs namenode -f
docker logs datanode -f
```

---

## 🎯 Prochaines Étapes (Extensions possibles)

### Étape 4 - Traitement des données
- **Apache Spark** : Traitement distribué
- **Nettoyage** : Validation et filtrage
- **Agrégation** : Statistiques par zone/période

### Étape 5 - Analytics
- **Tableaux de bord** : Grafana + Kibana
- **Alertes** : Détection de congestions
- **ML** : Prédictions de trafic

### Étape 6 - Production
- **Sécurité** : Authentication, encryption
- **Scalabilité** : Cluster multi-nœuds
- **Monitoring** : Prometheus + AlertManager

---

## 📞 Support

### Documentation technique
- **Apache Kafka** : https://kafka.apache.org/documentation/
- **Apache Hadoop HDFS** : https://hadoop.apache.org/docs/stable/
- **Apache Airflow** : https://airflow.apache.org/docs/

### Issues et contributions
- Signaler les problèmes via GitHub Issues
- Contribuer via Pull Requests

---

## 📜 Licence

Ce projet est sous licence MIT - voir fichier LICENSE pour détails.

---

## 👥 Auteurs

Projet réalisé dans le cadre du devoir Big Data - Smart City Traffic Analysis.

**Data Engineer** : Pipeline End-to-End pour l'analyse du trafic urbain intelligent.

---

*🚦 Made with ❤️ for Smart Cities*
