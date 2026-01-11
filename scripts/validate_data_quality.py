#!/usr/bin/env python3
"""
Validation de la qualité des données - Version Corrigée
Script de vérification pour le pipeline Smart City
"""

import requests
import json
import sys
import argparse
from datetime import datetime

class DataQualityValidator:
    """Validateur de qualité des données du pipeline"""
    
    def __init__(self, hdfs_namenode: str = "http://namenode:9870"):
        self.hdfs_namenode = hdfs_namenode
        self.validation_results = []
    
    def check_hdfs_path(self, path: str, min_items: int = 1) -> bool:
        """
        Vérifie qu'un chemin HDFS existe et contient des éléments (fichiers ou dossiers)
        """
        try:
            # Appel à l'API WebHDFS
            url = f"{self.hdfs_namenode}/webhdfs/v1{path}?op=LISTSTATUS"
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                self.validation_results.append({
                    'check': f'HDFS Path: {path}',
                    'status': 'FAIL',
                    'message': f'Chemin non trouvé ou inaccessible (HTTP {response.status_code})'
                })
                return False
            
            data = response.json()
            items = data.get('FileStatuses', {}).get('FileStatus', [])
            count = len(items)
            
            if count < min_items:
                self.validation_results.append({
                    'check': f'HDFS Path: {path}',
                    'status': 'FAIL',
                    'message': f'Attendu au moins {min_items} éléments, trouvé {count}'
                })
                return False
            
            self.validation_results.append({
                'check': f'HDFS Path: {path}',
                'status': 'PASS',
                'message': f'Trouvé {count} éléments (fichiers/dossiers)'
            })
            return True
            
        except Exception as e:
            self.validation_results.append({
                'check': f'HDFS Path: {path}',
                'status': 'ERROR',
                'message': str(e)
            })
            return False

    def validate_all(self) -> bool:
        """Exécute toutes les validations"""
        print("=" * 80)
        print("VALIDATION DE LA QUALITÉ DES DONNÉES - SMART CITY PIPELINE")
        print("=" * 80)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"HDFS NameNode: {self.hdfs_namenode}")
        
        # 1. Vérifie si les données brutes sont là (dossiers de zones)
        raw_ok = self.check_hdfs_path("/data/raw/traffic")
        
        # 2. Vérifie si Spark a créé les résultats (Processed)
        processed_ok = self.check_hdfs_path("/data/processed/traffic/zone_metrics")
        
        # 3. Vérifie si la zone Analytics est prête (Parquet)
        analytics_ok = self.check_hdfs_path("/data/analytics/traffic/zone_metrics")
        
        # Affichage du résumé
        print("\n" + "=" * 80)
        print("RÉSUMÉ DE LA VALIDATION")
        print("=" * 80)
        
        for result in self.validation_results:
            status_symbol = "✓" if result['status'] == 'PASS' else "✗"
            print(f"{status_symbol} {result['check']}: {result['status']}")
            if result['status'] != 'PASS':
                print(f"  → {result['message']}")
        
        all_passed = raw_ok and processed_ok and analytics_ok
        
        if all_passed:
            print("\n✓ VALIDATION RÉUSSIE - Pipeline opérationnel")
        else:
            print("\n✗ VALIDATION ÉCHOUÉE")
            
        return all_passed

def main():
    parser = argparse.ArgumentParser(description='Validation du pipeline Smart City')
    parser.add_argument('--hdfs-namenode', default='http://namenode:9870', help='URL WebHDFS')
    args = parser.parse_args()
    
    validator = DataQualityValidator(hdfs_namenode=args.hdfs_namenode)
    success = validator.validate_all()
    
    # Exit 0 si succès, 1 si échec pour Airflow
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()