#!/usr/bin/env python3
"""
Consumer Kafka pour stocker les données dans HDFS via API REST
Étape 3 : Stockage des données brutes (Data Lake - Raw Zone)
"""

import json
import sys
import argparse
import requests
import os
from datetime import datetime
from kafka import KafkaConsumer


class HDFSRestClient:
    """Client HDFS via API REST"""
    
    def __init__(self, namenode_host='namenode', namenode_port=9870, user='root'):
        self.base_url = f"http://{namenode_host}:{namenode_port}/webhdfs/v1"
        self.user = user
        print(f"Client HDFS REST initialisé: {self.base_url}")
    
    def mkdir(self, path):
        """Crée un répertoire HDFS"""
        try:
            url = f"{self.base_url}{path}?op=MKDIRS&user.name={self.user}"
            response = requests.put(url, timeout=10)
            if response.status_code in [200, 201]:
                print(f"Répertoire HDFS créé: {path}")
                return True
            else:
                print(f"Erreur création répertoire {path}: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"Erreur lors de la création du répertoire {path}: {e}")
            return False
    
    def create_file(self, path, content):
        """Crée un fichier HDFS"""
        try:
            url = f"{self.base_url}{path}?op=CREATE&user.name={self.user}&overwrite=true"
            headers = {'Content-Type': 'application/json'}
            response = requests.put(url, data=content, headers=headers, timeout=30)
            if response.status_code in [200, 201]:
                print(f"Fichier créé dans HDFS: {path}")
                return True
            else:
                print(f"Erreur création fichier {path}: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"Erreur lors de la création du fichier {path}: {e}")
            return False
    
    def list_directory(self, path):
        """Liste le contenu d'un répertoire HDFS"""
        try:
            url = f"{self.base_url}{path}?op=LISTSTATUS&user.name={self.user}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Erreur listing {path}: {response.status_code}")
                return None
        except Exception as e:
            print(f"Erreur lors du listing {path}: {e}")
            return None


def get_hdfs_path(zone, date_str):
    """Génère le chemin HDFS pour une zone et une date"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"/data/raw/traffic/{zone}/{date_str}/traffic_events_{timestamp}.json"


def consume_kafka_to_hdfs(bootstrap_servers, hdfs_client, batch_size=20, timeout=60):
    """Consomme TOUS les messages Kafka et les stocke dans HDFS"""
    
    # Initialiser le consumer Kafka
    try:
        consumer = KafkaConsumer(
            'traffic-events',
            bootstrap_servers=bootstrap_servers,
            auto_offset_reset='earliest',
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            key_deserializer=lambda x: x.decode('utf-8') if x else None,
            group_id='hdfs-consumer-all',
            enable_auto_commit=True,
            consumer_timeout_ms=timeout * 1000  # Timeout en millisecondes
        )
        print(f"Consumer Kafka initialisé: {bootstrap_servers}")
        print(f"Topic: traffic-events")
        print(f"Groupe: hdfs-consumer-all")
        print("Mode: CONSOMMATION COMPLÈTE de tous les messages")
    except Exception as e:
        print(f"Erreur lors de l'initialisation du consumer Kafka: {e}")
        return False
    
    # Créer le répertoire racine
    hdfs_client.mkdir("/data/raw/traffic")
    
    messages_by_zone = {}
    total_messages = 0
    last_progress_time = datetime.now()
    
    try:
        print("Démarrage de la consommation complète...")
        print(f"Batch size: {batch_size} messages")
        print(f"Timeout: {timeout} secondes sans nouveau message")
        print("Appuyez Ctrl+C pour arrêter manuellement\n")
        
        while True:
            try:
                # Poll pour obtenir des messages avec timeout
                message_batch = consumer.poll(timeout_ms=5000)
                
                if not message_batch:
                    # Vérifier si on a dépassé le timeout global
                    time_since_last = (datetime.now() - last_progress_time).seconds
                    if time_since_last > timeout:
                        print(f"\nTimeout de {timeout}s sans nouveau message. Arrêt de la consommation.")
                        break
                    continue
                
                # Traiter les messages reçus
                for topic_partition, messages in message_batch.items():
                    for message in messages:
                        # Extraire les données du message
                        zone = message.value.get('zone', 'unknown')
                        date_str = datetime.now().strftime("%Y/%m/%d")
                        
                        # Regrouper par zone
                        if zone not in messages_by_zone:
                            messages_by_zone[zone] = []
                        
                        messages_by_zone[zone].append(message.value)
                        total_messages += 1
                        last_progress_time = datetime.now()
                        
                        # Afficher la progression toutes les 50 messages
                        if total_messages % 50 == 0:
                            print(f"Progression: {total_messages} messages consommés")
                        
                        # Stocker en batch quand on atteint la taille du batch
                        if len(messages_by_zone[zone]) >= batch_size:
                            hdfs_path = get_hdfs_path(zone, date_str)
                            json_content = '\n'.join([json.dumps(msg, ensure_ascii=False) for msg in messages_by_zone[zone]])
                            
                            # Créer le répertoire de la zone
                            zone_dir = f"/data/raw/traffic/{zone}/{date_str}"
                            hdfs_client.mkdir(zone_dir)
                            
                            # Créer le fichier
                            hdfs_client.create_file(hdfs_path, json_content)
                            print(f"✅ Batch de {len(messages_by_zone[zone])} messages stocké pour {zone}")
                            messages_by_zone[zone] = []
                        
            except KeyboardInterrupt:
                print(f"\nArrêt manuel demandé. Total messages traités: {total_messages}")
                break
            except Exception as e:
                print(f"Erreur lors du traitement: {e}")
                continue
                
    except Exception as e:
        print(f"Erreur lors de la consommation Kafka: {e}")
    
    # Stocker les messages restants
    remaining_total = sum(len(msgs) for msgs in messages_by_zone.values())
    if remaining_total > 0:
        print(f"\nStockage des {remaining_total} messages restants...")
        for zone, messages in messages_by_zone.items():
            if messages:
                date_str = datetime.now().strftime("%Y/%m/%d")
                hdfs_path = get_hdfs_path(zone, date_str)
                json_content = '\n'.join([json.dumps(msg, ensure_ascii=False) for msg in messages])
                
                # Créer le répertoire de la zone
                zone_dir = f"/data/raw/traffic/{zone}/{date_str}"
                hdfs_client.mkdir(zone_dir)
                
                # Créer le fichier
                hdfs_client.create_file(hdfs_path, json_content)
                print(f"✅ Dernier batch de {len(messages)} messages stocké pour {zone}")
    
    consumer.close()
    print(f"\n🎉 CONSOMMATION TERMINÉE! Total: {total_messages} messages")
    return True


def verify_hdfs_storage(hdfs_client):
    """Vérifie le stockage dans HDFS"""
    try:
        print("\n=== VÉRIFICATION HDFS ===")
        
        # Lister le contenu de /data/raw/traffic
        result = hdfs_client.list_directory("/data/raw/traffic")
        if result and 'FileStatuses' in result:
            files = result['FileStatuses']
            print(f"Fichiers trouvés dans /data/raw/traffic: {len(files)}")
            
            for file_info in files:
                print(f"  - {file_info['pathSuffix']} ({file_info['length']} bytes)")
        else:
            print("Le répertoire /data/raw/traffic n'existe pas ou est vide")
            
    except Exception as e:
        print(f"Erreur lors de la vérification HDFS: {e}")


def main():
    parser = argparse.ArgumentParser(description='Consumer Kafka pour stockage HDFS - CONSOMMATION COMPLÈTE')
    parser.add_argument('--bootstrap-servers', default='kafka:29092',
                       help='Serveurs Kafka bootstrap')
    parser.add_argument('--namenode-host', default='namenode',
                       help='HDFS NameNode host')
    parser.add_argument('--namenode-port', type=int, default=9870,
                       help='HDFS NameNode port')
    parser.add_argument('--batch-size', type=int, default=20,
                       help='Taille des batchs pour stockage HDFS')
    parser.add_argument('--timeout', type=int, default=60,
                       help='Timeout en secondes sans nouveau message')
    
    args = parser.parse_args()
    
    print("=== Consumer Kafka vers HDFS (CONSOMMATION COMPLÈTE) ===")
    print(f"Serveurs Kafka: {args.bootstrap_servers}")
    print(f"NameNode HDFS: {args.namenode_host}:{args.namenode_port}")
    print(f"Mode: TOUS les messages du topic 'traffic-events'")
    
    # Initialiser HDFS
    hdfs_client = HDFSRestClient(args.namenode_host, args.namenode_port)
    if not hdfs_client:
        sys.exit(1)
    
    # Consommer TOUS les messages
    success = consume_kafka_to_hdfs(
        args.bootstrap_servers, 
        hdfs_client, 
        args.batch_size,
        args.timeout
    )
    
    if success:
        # Vérifier le stockage
        verify_hdfs_storage(hdfs_client)
        print("\n=== Stockage HDFS terminé avec succès ===")
    else:
        print("\n=== Échec du stockage HDFS ===")
        sys.exit(1)


if __name__ == '__main__':
    main()
