#!/usr/bin/env python3
"""
Producteur Kafka simple pour les données de trafic Smart City
Étape 2: Ingestion des données (Streaming Kafka) - Version simplifiée
"""

import json
import time
import random
from datetime import datetime
from kafka import KafkaProducer
from kafka.errors import KafkaError


def generate_simple_event():
    """Génère un événement de trafic simple"""
    zones = ["Centre-ville", "Peripherie", "Zone industrielle", 
              "Quartier residentiel", "Zone commerciale", "Universite", "Aeroport"]
    
    road_types = ["autoroute", "avenue", "rue"]
    
    event = {
        "sensor_id": f"SENSOR_{random.randint(1, 999):03d}",
        "road_id": f"ROAD_{random.randint(1, 999):03d}",
        "road_type": random.choice(road_types),
        "zone": random.choice(zones),
        "vehicle_count": random.randint(5, 200),
        "average_speed": round(random.uniform(10, 130), 1),
        "occupancy_rate": round(random.uniform(0.05, 0.95), 3),
        "event_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return event


class SimpleKafkaProducer:
    """Producteur Kafka simplifié"""
    
    def __init__(self, bootstrap_servers="localhost:9092", topic="traffic-events"):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        
        # Configuration du producteur Kafka
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            acks='all',
            retries=3,
            compression_type='gzip'
        )
        
        print(f"Producteur Kafka initialise")
        print(f"Serveurs: {bootstrap_servers}")
        print(f"Topic: {topic}")
    
    def send_events(self, events_per_second=1, duration=60):
        """Envoie des événements vers Kafka"""
        print(f"Demarrage du streaming Kafka")
        print(f"Frequence: {events_per_second} evenements/seconde")
        print(f"Duree: {duration} secondes")
        
        event_interval = 1.0 / events_per_second
        start_time = time.time()
        events_sent = 0
        
        try:
            while time.time() - start_time < duration:
                # Générer un événement
                event = generate_simple_event()
                
                try:
                    # Envoyer vers Kafka
                    partition_key = event.get('zone', 'unknown')
                    future = self.producer.send(
                        topic=self.topic,
                        key=partition_key,
                        value=event
                    )
                    
                    # Attendre la confirmation
                    record_metadata = future.get(timeout=5)
                    
                    print(f"Message envoye: {event['sensor_id']} -> "
                          f"Partition {record_metadata.partition}")
                    
                    events_sent += 1
                    
                except Exception as e:
                    print(f"Erreur envoi: {e}")
                
                # Pause pour respecter la fréquence
                time.sleep(event_interval)
                
                # Affichage de progression
                if events_sent % 5 == 0:
                    elapsed = time.time() - start_time
                    rate = events_sent / elapsed
                    print(f"Progression: {events_sent} messages envoyes ({rate:.1f} msg/s)")
        
        except KeyboardInterrupt:
            print(f"\nArret demande. Messages envoyes: {events_sent}")
        
        finally:
            self.producer.flush()
            self.producer.close()
        
        print(f"Streaming termine! Total: {events_sent} messages envoyes")
        return events_sent


def main():
    """Point d'entrée principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Producteur Kafka simple pour les données de trafic')
    parser.add_argument('--bootstrap-servers', type=str, default='localhost:9092')
    parser.add_argument('--topic', type=str, default='traffic-events')
    parser.add_argument('--events-per-second', type=int, default=1)
    parser.add_argument('--duration', type=int, default=60)
    
    args = parser.parse_args()
    
    # Création et démarrage du producteur
    producer = SimpleKafkaProducer(
        bootstrap_servers=args.bootstrap_servers,
        topic=args.topic
    )
    
    events_sent = producer.send_events(
        events_per_second=args.events_per_second,
        duration=args.duration
    )
    
    print("Producteur Kafka termine")


if __name__ == '__main__':
    main()
