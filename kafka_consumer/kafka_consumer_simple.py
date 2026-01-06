#!/usr/bin/env python3
"""
Consumer Kafka simple pour les données de trafic Smart City
Étape 2: Ingestion des données (Streaming Kafka) - Test de réception
"""

import json
import time
import argparse
from kafka import KafkaConsumer


class SimpleKafkaConsumer:
    """Consumer Kafka simplifié"""
    
    def __init__(self, bootstrap_servers="localhost:9092", topic="traffic-events", group_id="test-consumer"):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.group_id = group_id
        
        # Configuration du consumer Kafka
        self.consumer = KafkaConsumer(
            topic,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            value_deserializer=lambda v: json.loads(v.decode('utf-8')),
            key_deserializer=lambda k: k.decode('utf-8') if k else None,
            auto_offset_reset='earliest',
            enable_auto_commit=True
        )
        
        print(f"Consumer Kafka initialise")
        print(f"Serveurs: {bootstrap_servers}")
        print(f"Topic: {topic}")
        print(f"Groupe: {group_id}")
    
    def consume_messages(self, max_messages=20, timeout=30):
        """Consomme les messages depuis Kafka"""
        print(f"Demarrage de la consommation...")
        print(f"Messages maximum: {max_messages}")
        print(f"Timeout: {timeout} secondes")
        print("=" * 60)
        
        messages_consumed = 0
        start_time = time.time()
        
        try:
            for message in self.consumer:
                # Afficher le message reçu
                print(f"Message #{messages_consumed + 1}:")
                print(f"  Partition: {message.partition}")
                print(f"  Offset: {message.offset}")
                print(f"  Cle: {message.key}")
                print(f"  Sensor ID: {message.value.get('sensor_id', 'N/A')}")
                print(f"  Zone: {message.value.get('zone', 'N/A')}")
                print(f"  Vehicules: {message.value.get('vehicle_count', 'N/A')}")
                print(f"  Vitesse: {message.value.get('average_speed', 'N/A')} km/h")
                print(f"  Heure: {message.value.get('event_time', 'N/A')}")
                print("-" * 40)
                
                messages_consumed += 1
                
                # Arrêter après le nombre maximum de messages
                if messages_consumed >= max_messages:
                    break
                
                # Arrêter après le timeout
                if time.time() - start_time > timeout:
                    break
        
        except KeyboardInterrupt:
            print(f"\nArret demande. Messages consommes: {messages_consumed}")
        
        finally:
            self.consumer.close()
        
        print(f"Consommation terminee! Total: {messages_consumed} messages")
        return messages_consumed


def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(description='Consumer Kafka simple pour les données de trafic')
    parser.add_argument('--bootstrap-servers', type=str, default='localhost:9092')
    parser.add_argument('--topic', type=str, default='traffic-events')
    parser.add_argument('--group-id', type=str, default='test-consumer')
    parser.add_argument('--max-messages', type=int, default=20)
    parser.add_argument('--timeout', type=int, default=30)
    
    args = parser.parse_args()
    
    # Création et démarrage du consumer
    consumer = SimpleKafkaConsumer(
        bootstrap_servers=args.bootstrap_servers,
        topic=args.topic,
        group_id=args.group_id
    )
    
    messages_consumed = consumer.consume_messages(
        max_messages=args.max_messages,
        timeout=args.timeout
    )
    
    print("Consumer Kafka termine")


if __name__ == '__main__':
    main()
