#!/usr/bin/env python3
"""
Conversion des données traitées au format Parquet
Étape 5: Analytics Zone - Structuration analytique

Objectif: Convertir les données JSON traitées en format Parquet optimisé
          pour l'analyse et les requêtes rapides.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col
import argparse
import sys


class ParquetConverter:
    """Convertisseur de données JSON vers Parquet pour la zone analytics"""
    
    def __init__(self, hdfs_namenode: str = "hdfs://namenode:9000"):
        """
        Initialise le convertisseur
        
        Args:
            hdfs_namenode: URL du NameNode HDFS
        """
        self.hdfs_namenode = hdfs_namenode
        self.spark = self._create_spark_session()
    
    def _create_spark_session(self) -> SparkSession:
        """Crée une session Spark configurée pour HDFS et Parquet"""
        return SparkSession.builder \
            .appName("SmartCity_Parquet_Converter") \
            .master("local[*]") \
            .config("spark.hadoop.fs.defaultFS", self.hdfs_namenode) \
            .config("spark.sql.parquet.compression.codec", "snappy") \
            .config("spark.sql.parquet.mergeSchema", "false") \
            .config("spark.sql.parquet.filterPushdown", "true") \
            .config("spark.driver.memory", "2g") \
            .getOrCreate()
    
    def convert_to_parquet(self, input_path: str, output_path: str, dataset_name: str):
        """
        Convertit un dataset JSON en Parquet
        
        Args:
            input_path: Chemin HDFS du fichier JSON source
            output_path: Chemin HDFS de base pour la sortie
            dataset_name: Nom du dataset
        """
        full_input = f"{self.hdfs_namenode}{input_path}/{dataset_name}"
        full_output = f"{self.hdfs_namenode}{output_path}/{dataset_name}"
        
        print(f"\nConversion: {dataset_name}")
        print(f"  Source: {full_input}")
        print(f"  Destination: {full_output}")
        
        try:
            # Lire le JSON
            df = self.spark.read.json(full_input)
            count = df.count()
            
            if count == 0:
                print(f"  ATTENTION: Aucune donnée dans {dataset_name}")
                return
            
            print(f"  Lignes lues: {count}")
            
            # Afficher le schéma
            print(f"  Schéma:")
            df.printSchema()
            
            # Sauvegarder en Parquet avec compression Snappy
            df.write.mode("overwrite") \
                .option("compression", "snappy") \
                .parquet(full_output)
            
            # Vérifier la sauvegarde
            df_verify = self.spark.read.parquet(full_output)
            verify_count = df_verify.count()
            
            print(f"  ✓ Conversion réussie: {verify_count} lignes")
            
            # Afficher les statistiques du fichier Parquet
            print(f"  Format: Parquet avec compression Snappy")
            
        except Exception as e:
            print(f"  ✗ Erreur lors de la conversion: {e}")
            import traceback
            traceback.print_exc()
    
    def convert_all(self, processed_path: str = "/data/processed/traffic",
                   analytics_path: str = "/data/analytics/traffic"):
        """
        Convertit tous les datasets traités en Parquet
        
        Args:
            processed_path: Chemin des données traitées (JSON)
            analytics_path: Chemin de sortie analytics (Parquet)
        """
        print("=" * 80)
        print("CONVERSION VERS ZONE ANALYTICS - FORMAT PARQUET")
        print("=" * 80)
        
        datasets = [
            "zone_metrics",
            "road_metrics",
            "congestion_analysis",
            "hourly_patterns"
        ]
        
        success_count = 0
        
        for dataset in datasets:
            try:
                self.convert_to_parquet(processed_path, analytics_path, dataset)
                success_count += 1
            except Exception as e:
                print(f"Erreur pour {dataset}: {e}")
        
        print("\n" + "=" * 80)
        print(f"CONVERSION TERMINÉE: {success_count}/{len(datasets)} datasets convertis")
        print("=" * 80)
        print(f"Données Parquet disponibles dans: {self.hdfs_namenode}{analytics_path}")
        
        # Justification du format Parquet
        print("\n📊 JUSTIFICATION DU FORMAT PARQUET:")
        print("  • Compression: Réduction de 70-90% de la taille vs JSON")
        print("  • Performance: Lecture columnaire 10-100x plus rapide")
        print("  • Schéma: Typage fort et validation automatique")
        print("  • Compatibilité: Support natif Spark, Hive, Presto, etc.")
        print("  • Optimisation: Predicate pushdown et column pruning")
        
        self.spark.stop()


def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(
        description='Conversion des données traitées vers format Parquet'
    )
    parser.add_argument(
        '--hdfs-namenode',
        default='hdfs://namenode:9000',
        help='URL du NameNode HDFS'
    )
    parser.add_argument(
        '--processed-path',
        default='/data/processed/traffic',
        help='Chemin HDFS des données traitées (JSON)'
    )
    parser.add_argument(
        '--analytics-path',
        default='/data/analytics/traffic',
        help='Chemin HDFS de sortie analytics (Parquet)'
    )
    
    args = parser.parse_args()
    
    # Créer et exécuter le convertisseur
    converter = ParquetConverter(hdfs_namenode=args.hdfs_namenode)
    converter.convert_all(
        processed_path=args.processed_path,
        analytics_path=args.analytics_path
    )


if __name__ == '__main__':
    main()
