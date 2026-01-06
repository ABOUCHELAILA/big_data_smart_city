#!/usr/bin/env python3
"""
Générateur de données de trafic urbain pour Smart City
Étape 1: Génération des données (Simulation Smart City)

Objectif: Simuler un réseau réel de capteurs urbains générant des événements de trafic en continu.
"""

import json
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List
import argparse


class TrafficDataGenerator:
    """Générateur d'événements de trafic réalistes pour Smart City"""
    
    def __init__(self, num_sensors: int = 50):
        """
        Initialise le générateur de données
        
        Args:
            num_sensors: Nombre de capteurs à simuler
        """
        self.num_sensors = num_sensors
        self.sensors = self._initialize_sensors()
        self.current_time = datetime.now()
        
        print(f"Generateur initialise avec {num_sensors} capteurs")
    
    def _initialize_sensors(self) -> List[Dict]:
        """Initialise la configuration des capteurs répartis dans la ville"""
        sensors = []
        
        # Zones géographiques de la Smart City (sans accents pour compatibilité)
        zones = ["Centre-ville", "Peripherie", "Zone industrielle", 
                "Quartier residentiel", "Zone commerciale", "Universite", "Aeroport"]
        
        # Types de routes selon la classification urbaine
        road_types = ["autoroute", "avenue", "rue"]
        
        for i in range(1, self.num_sensors + 1):
            sensor = {
                "sensor_id": f"SENSOR_{i:03d}",
                "road_id": f"ROAD_{random.randint(1, 100):03d}",
                "road_type": random.choice(road_types),
                "zone": random.choice(zones)
            }
            sensors.append(sensor)
        
        return sensors
    
    def _get_traffic_factor_by_hour(self, hour: int) -> float:
        """
        Calcule le facteur de trafic selon l'heure (simulation réaliste)
        
        Args:
            hour: Heure de la journée (0-23)
            
        Returns:
            Facteur de trafic (0.1 à 1.0)
        """
        # Heures de pointe: 7-9h et 17-19h
        if 7 <= hour <= 9 or 17 <= hour <= 19:
            return 1.0  # Trafic maximal
        elif 10 <= hour <= 16:
            return 0.7  # Trafic modéré
        elif 20 <= hour <= 22:
            return 0.5  # Trafic faible
        else:  # 23-6h
            return 0.2  # Trafic très faible
    
    def _get_speed_limits(self, road_type: str) -> tuple:
        """
        Retourne les limites de vitesse selon le type de route
        
        Args:
            road_type: Type de route
            
        Returns:
            Tuple (vitesse_min, vitesse_max) en km/h
        """
        speed_limits = {
            "autoroute": (80, 130),
            "avenue": (40, 70),
            "rue": (20, 50)
        }
        return speed_limits.get(road_type, (30, 60))
    
    def _generate_realistic_metrics(self, sensor: Dict) -> Dict:
        """
        Génère des métriques de trafic réalistes
        
        Args:
            sensor: Configuration du capteur
            
        Returns:
            Dictionnaire avec les métriques calculées
        """
        current_hour = self.current_time.hour
        traffic_factor = self._get_traffic_factor_by_hour(current_hour)
        
        # Limites de vitesse selon le type de route
        min_speed, max_speed = self._get_speed_limits(sensor["road_type"])
        
        # Nombre de véhicules (variable selon l'heure et le type de route)
        base_vehicles = {
            "autoroute": 150,
            "avenue": 80,
            "rue": 40
        }
        
        vehicle_count = int(base_vehicles[sensor["road_type"]] * traffic_factor)
        vehicle_count = max(5, vehicle_count + random.randint(-10, 10))  # Variation aléatoire
        
        # Vitesse moyenne (inversement proportionnelle au trafic)
        traffic_density = vehicle_count / base_vehicles[sensor["road_type"]]
        speed_reduction = traffic_density * 0.5  # Plus de trafic = moins de vitesse
        
        average_speed = max_speed * (1 - speed_reduction)
        average_speed = max(min_speed, average_speed + random.uniform(-5, 5))
        average_speed = round(average_speed, 1)
        
        # Taux d'occupation (proportionnel au nombre de véhicules)
        occupancy_rate = min(0.95, traffic_density + random.uniform(-0.1, 0.1))
        occupancy_rate = max(0.05, occupancy_rate)
        occupancy_rate = round(occupancy_rate, 3)
        
        return {
            "vehicle_count": vehicle_count,
            "average_speed": average_speed,
            "occupancy_rate": occupancy_rate
        }
    
    def generate_event(self) -> Dict:
        """
        Génère un événement de trafic complet selon la structure obligatoire
        
        Returns:
            Dictionnaire représentant un événement de trafic au format JSON requis
        """
        # Sélection aléatoire d'un capteur
        sensor = random.choice(self.sensors)
        
        # Génération des métriques réalistes
        metrics = self._generate_realistic_metrics(sensor)
        
        # Construction de l'événement selon la structure OBLIGATOIRE
        event = {
            "sensor_id": sensor["sensor_id"],
            "road_id": sensor["road_id"],
            "road_type": sensor["road_type"],
            "zone": sensor["zone"],
            "vehicle_count": metrics["vehicle_count"],
            "average_speed": metrics["average_speed"],
            "occupancy_rate": metrics["occupancy_rate"],
            "event_time": self.current_time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Avancer le temps pour le prochain événement
        self.current_time += timedelta(seconds=random.randint(1, 3))
        
        return event
    
    def generate_stream(self, events_per_second: int = 1, duration: int = 60, 
                      output_file: str = None) -> List[Dict]:
        """
        Génère un flux continu d'événements de trafic
        
        Args:
            events_per_second: Nombre d'événements par seconde
            duration: Durée en secondes
            output_file: Fichier de sortie optionnel
            
        Returns:
            Liste des événements générés
        """
        print(f"Generation de {events_per_second} evenements/seconde pendant {duration} secondes...")
        print(f"Capteurs simules: {self.num_sensors}")
        print(f"Heure de debut: {self.current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        events = []
        event_interval = 1.0 / events_per_second
        start_time = time.time()
        
        try:
            while time.time() - start_time < duration:
                # Générer un événement
                event = self.generate_event()
                events.append(event)
                
                # Affichage de l'événement généré
                print(f"{event['sensor_id']} | {event['zone']} | "
                      f"{event['vehicle_count']} vehicules | "
                      f"{event['average_speed']} km/h | "
                      f"{event['event_time']}")
                
                # Écrire dans le fichier si spécifié
                if output_file:
                    with open(output_file, 'a') as f:
                        f.write(json.dumps(event) + '\n')
                
                # Pause pour respecter le rythme
                time.sleep(event_interval)
                
                # Affichage de progression
                if len(events) % 10 == 0:
                    elapsed = time.time() - start_time
                    rate = len(events) / elapsed
                    print(f"Progression: {len(events)} evenements ({rate:.1f} evt/s)")
        
        except KeyboardInterrupt:
            print(f"\nArret demande. Evenements generes: {len(events)}")
        
        print(f"Generation terminee! Total: {len(events)} evenements")
        
        # Afficher un résumé statistique
        if events:
            self._print_summary(events)
        
        return events
    
    def _print_summary(self, events: List[Dict]):
        """Affiche un résumé statistique des événements générés"""
        print("\nRESUME STATISTIQUE:")
        
        # Répartition par zone
        zones = {}
        for event in events:
            zone = event["zone"]
            zones[zone] = zones.get(zone, 0) + 1
        
        print("Repartition par zone:")
        for zone, count in sorted(zones.items()):
            print(f"  • {zone}: {count} evenements")
        
        # Répartition par type de route
        road_types = {}
        for event in events:
            road_type = event["road_type"]
            road_types[road_type] = road_types.get(road_type, 0) + 1
        
        print("\nRepartition par type de route:")
        for road_type, count in sorted(road_types.items()):
            print(f"  • {road_type}: {count} evenements")
        
        # Statistiques de trafic
        vehicle_counts = [event["vehicle_count"] for event in events]
        avg_vehicles = sum(vehicle_counts) / len(vehicle_counts)
        max_vehicles = max(vehicle_counts)
        min_vehicles = min(vehicle_counts)
        
        print(f"\nStatistiques vehicules:")
        print(f"  • Moyenne: {avg_vehicles:.1f} vehicules")
        print(f"  • Maximum: {max_vehicles} vehicules")
        print(f"  • Minimum: {min_vehicles} vehicules")
        
        # Statistiques de vitesse
        speeds = [event["average_speed"] for event in events]
        avg_speed = sum(speeds) / len(speeds)
        
        print(f"\nStatistiques vitesse:")
        print(f"  • Moyenne: {avg_speed:.1f} km/h")


def main():
    """Point d'entrée principal du générateur"""
    parser = argparse.ArgumentParser(description='Générateur de données de trafic Smart City')
    parser.add_argument('--sensors', type=int, default=50,
                       help='Nombre de capteurs à simuler (défaut: 50)')
    parser.add_argument('--events-per-second', type=int, default=1,
                       help='Nombre d\'événements par seconde (défaut: 1)')
    parser.add_argument('--duration', type=int, default=60,
                       help='Durée en secondes (défaut: 60)')
    parser.add_argument('--output', type=str,
                       help='Fichier de sortie pour les événements (optionnel)')
    
    args = parser.parse_args()
    
    # Création du générateur
    generator = TrafficDataGenerator(num_sensors=args.sensors)
    
    # Génération du flux d'événements
    events = generator.generate_stream(
        events_per_second=args.events_per_second,
        duration=args.duration,
        output_file=args.output
    )
    
    print("Generation de données terminée")


if __name__ == '__main__':
    main()
