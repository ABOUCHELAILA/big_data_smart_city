#!/usr/bin/env python3
"""
Traitement des données de trafic avec Apache Spark
Étape 4: Data Processing

Objectif: Lire les données brutes depuis HDFS, calculer des agrégations et métriques,
          identifier les zones congestionnées, et sauvegarder les résultats.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, avg, sum as spark_sum, count, max as spark_max, min as spark_min,
    when, hour, to_timestamp, round as spark_round
)
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType
import argparse
import sys


class TrafficProcessor:
    """Processeur Spark pour l'analyse du trafic urbain"""
    
    def __init__(self, hdfs_namenode: str = "hdfs://namenode:9000"):
        """
        Initialise le processeur Spark
        
        Args:
            hdfs_namenode: URL du NameNode HDFS
        """
        self.hdfs_namenode = hdfs_namenode
        self.spark = self._create_spark_session()
        
    def _create_spark_session(self) -> SparkSession:
        """Crée une session Spark configurée pour HDFS"""
        return SparkSession.builder \
            .appName("SmartCity_Traffic_Processing") \
            .master("local[*]") \
            .config("spark.hadoop.fs.defaultFS", self.hdfs_namenode) \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .config("spark.driver.memory", "2g") \
            .getOrCreate()
    
    def read_raw_data(self, raw_path: str = "/data/raw/traffic"):
        """
        Lit les données brutes depuis HDFS
        
        Args:
            raw_path: Chemin HDFS des données brutes
            
        Returns:
            DataFrame Spark avec les données de trafic
        """
        print(f"Lecture des données depuis {self.hdfs_namenode}{raw_path}")
        
        # Schéma des données de trafic
        schema = StructType([
            StructField("sensor_id", StringType(), True),
            StructField("road_id", StringType(), True),
            StructField("road_type", StringType(), True),
            StructField("zone", StringType(), True),
            StructField("vehicle_count", IntegerType(), True),
            StructField("average_speed", DoubleType(), True),
            StructField("occupancy_rate", DoubleType(), True),
            StructField("event_time", StringType(), True)
        ])
        
        # Lecture récursive de tous les fichiers JSON
        full_path = f"{self.hdfs_namenode}{raw_path}/*/*/*/*/*.json"
        
        try:
            df = self.spark.read.schema(schema).json(full_path)
            count = df.count()
            print(f"Données lues: {count} événements")
            return df
        except Exception as e:
            print(f"Erreur lors de la lecture: {e}")
            # Essayer sans la structure de répertoires complète
            try:
                alt_path = f"{self.hdfs_namenode}{raw_path}/*/*.json"
                df = self.spark.read.schema(schema).json(alt_path)
                count = df.count()
                print(f"Données lues (chemin alternatif): {count} événements")
                return df
            except Exception as e2:
                print(f"Erreur alternative: {e2}")
                raise
    
    def calculate_zone_metrics(self, df):
        """
        Calcule les métriques de trafic par zone
        
        Args:
            df: DataFrame des données brutes
            
        Returns:
            DataFrame avec les métriques par zone
        """
        print("Calcul des métriques par zone...")
        
        zone_metrics = df.groupBy("zone").agg(
            spark_round(avg("vehicle_count"), 2).alias("avg_vehicle_count"),
            spark_round(avg("average_speed"), 2).alias("avg_speed"),
            spark_round(avg("occupancy_rate"), 3).alias("avg_occupancy_rate"),
            spark_max("vehicle_count").alias("max_vehicle_count"),
            spark_min("vehicle_count").alias("min_vehicle_count"),
            count("*").alias("total_events")
        ).orderBy(col("avg_vehicle_count").desc())
        
        print(f"Métriques calculées pour {zone_metrics.count()} zones")
        return zone_metrics
    
    def calculate_road_metrics(self, df):
        """
        Calcule les métriques par type de route
        
        Args:
            df: DataFrame des données brutes
            
        Returns:
            DataFrame avec les métriques par type de route
        """
        print("Calcul des métriques par type de route...")
        
        road_metrics = df.groupBy("road_type").agg(
            spark_round(avg("vehicle_count"), 2).alias("avg_vehicle_count"),
            spark_round(avg("average_speed"), 2).alias("avg_speed"),
            spark_round(avg("occupancy_rate"), 3).alias("avg_occupancy_rate"),
            count("*").alias("total_events")
        ).orderBy(col("avg_speed").desc())
        
        print(f"Métriques calculées pour {road_metrics.count()} types de routes")
        return road_metrics
    
    def identify_congestion(self, df, threshold: float = 0.7):
        """
        Identifie les zones à forte congestion
        
        Args:
            df: DataFrame des données brutes
            threshold: Seuil de taux d'occupation pour la congestion
            
        Returns:
            DataFrame des zones congestionnées
        """
        print(f"Identification des zones congestionnées (seuil: {threshold})...")
        
        # Marquer les événements congestionnés
        df_with_congestion = df.withColumn(
            "is_congested",
            when(col("occupancy_rate") >= threshold, 1).otherwise(0)
        )
        
        # Calculer le taux de congestion par zone
        congestion_metrics = df_with_congestion.groupBy("zone").agg(
            spark_round(avg("occupancy_rate"), 3).alias("avg_occupancy_rate"),
            spark_round(
                (spark_sum("is_congested") / count("*")) * 100, 2
            ).alias("congestion_percentage"),
            count("*").alias("total_events"),
            spark_sum("is_congested").alias("congested_events")
        ).orderBy(col("congestion_percentage").desc())
        
        print(f"Analyse de congestion pour {congestion_metrics.count()} zones")
        return congestion_metrics
    
    def calculate_hourly_patterns(self, df):
        """
        Analyse les patterns de trafic par heure
        
        Args:
            df: DataFrame des données brutes
            
        Returns:
            DataFrame avec les patterns horaires
        """
        print("Analyse des patterns horaires...")
        
        # Convertir event_time en timestamp et extraire l'heure
        df_with_hour = df.withColumn(
            "hour",
            hour(to_timestamp(col("event_time"), "yyyy-MM-dd HH:mm:ss"))
        )
        
        hourly_metrics = df_with_hour.groupBy("hour").agg(
            spark_round(avg("vehicle_count"), 2).alias("avg_vehicle_count"),
            spark_round(avg("average_speed"), 2).alias("avg_speed"),
            spark_round(avg("occupancy_rate"), 3).alias("avg_occupancy_rate"),
            count("*").alias("total_events")
        ).orderBy("hour")
        
        print(f"Patterns calculés pour {hourly_metrics.count()} heures")
        return hourly_metrics
    
    def save_processed_data(self, df, output_path: str, name: str):
        """
        Sauvegarde les données traitées dans HDFS
        
        Args:
            df: DataFrame à sauvegarder
            output_path: Chemin de base HDFS
            name: Nom du sous-répertoire
        """
        full_path = f"{self.hdfs_namenode}{output_path}/{name}"
        print(f"Sauvegarde des données dans {full_path}...")
        
        # Sauvegarder en JSON avec un seul fichier par partition
        df.coalesce(1).write.mode("overwrite").json(full_path)
        print(f"Données sauvegardées: {df.count()} lignes")
    
    def process_all(self, raw_path: str = "/data/raw/traffic",
                   output_path: str = "/data/processed/traffic"):
        """
        Exécute le pipeline complet de traitement
        
        Args:
            raw_path: Chemin des données brutes
            output_path: Chemin de sortie des données traitées
        """
        print("=" * 80)
        print("DÉMARRAGE DU TRAITEMENT SPARK - SMART CITY TRAFFIC")
        print("=" * 80)
        
        try:
            # 1. Lecture des données brutes
            df_raw = self.read_raw_data(raw_path)
            
            if df_raw.count() == 0:
                print("ATTENTION: Aucune donnée trouvée!")
                return
            
            # Afficher un échantillon
            print("\nÉchantillon des données brutes:")
            df_raw.show(5, truncate=False)
            
            # 2. Métriques par zone
            zone_metrics = self.calculate_zone_metrics(df_raw)
            print("\nMétriques par zone:")
            zone_metrics.show(truncate=False)
            self.save_processed_data(zone_metrics, output_path, "zone_metrics")
            
            # 3. Métriques par type de route
            road_metrics = self.calculate_road_metrics(df_raw)
            print("\nMétriques par type de route:")
            road_metrics.show(truncate=False)
            self.save_processed_data(road_metrics, output_path, "road_metrics")
            
            # 4. Analyse de congestion
            congestion = self.identify_congestion(df_raw)
            print("\nZones congestionnées:")
            congestion.show(truncate=False)
            self.save_processed_data(congestion, output_path, "congestion_analysis")
            
            # 5. Patterns horaires
            hourly = self.calculate_hourly_patterns(df_raw)
            print("\nPatterns horaires:")
            hourly.show(24, truncate=False)
            self.save_processed_data(hourly, output_path, "hourly_patterns")
            
            print("\n" + "=" * 80)
            print("TRAITEMENT TERMINÉ AVEC SUCCÈS")
            print("=" * 80)
            print(f"Données sauvegardées dans: {self.hdfs_namenode}{output_path}")
            
        except Exception as e:
            print(f"\nERREUR lors du traitement: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
        finally:
            self.spark.stop()


def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(
        description='Traitement Spark des données de trafic Smart City'
    )
    parser.add_argument(
        '--hdfs-namenode',
        default='hdfs://namenode:9000',
        help='URL du NameNode HDFS'
    )
    parser.add_argument(
        '--raw-path',
        default='/data/raw/traffic',
        help='Chemin HDFS des données brutes'
    )
    parser.add_argument(
        '--output-path',
        default='/data/processed/traffic',
        help='Chemin HDFS de sortie'
    )
    
    args = parser.parse_args()
    
    # Créer et exécuter le processeur
    processor = TrafficProcessor(hdfs_namenode=args.hdfs_namenode)
    processor.process_all(
        raw_path=args.raw_path,
        output_path=args.output_path
    )


if __name__ == '__main__':
    main()
