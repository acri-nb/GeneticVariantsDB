#!/usr/bin/env python3
"""
Script pour mesurer les temps de chargement des données par échantillon
pour comparer les performances avec l'ancienne version
"""

import pymysql
import pandas as pd
import time
from datetime import datetime
import csv

# Configuration de la connexion
DB_CONFIG = {
    'host': 'localhost',
    'user': 'usr',
    'password': 'usrpass',
    'database': 'vardb',
    'port': 3309
}

def read_regions(filepath='/Volumes/gth5TExt1/VS/IARC/HGDB/dash-files/regions.txt'):
    """Lire la liste des variants d'intérêt"""
    with open(filepath, 'r') as f:
        regions = [line.strip() for line in f if line.strip()]
    return regions

def read_cleared_samples(filepath='/Volumes/gth5TExt1/VS/IARC/HGDB/dash-files/cleared.tsv'):
    """Lire la liste des échantillons de référence"""
    with open(filepath, 'r') as f:
        samples = [line.strip() for line in f if line.strip()]
    return samples

def measure_sample_loading(conn, sample_name, regions):
    """Mesurer le temps de chargement pour un échantillon"""
    
    # 1. Mesurer le temps de requête pour récupérer les données
    query_start = time.time()
    
    query = """
    SELECT 
        v.name as variant,
        c.afreq,
        c.coverage,
        c.norm_count,
        g.name as gene
    FROM CallData c
    INNER JOIN VarData v ON v.id = c.variant
    INNER JOIN RunInfo r ON r.id = c.sample
    LEFT JOIN Genes g ON g.id = v.gene
    WHERE r.name = %s
    AND v.name IN ({})
    """.format(','.join(['%s'] * len(regions)))
    
    df = pd.read_sql(query, conn, params=[sample_name] + regions)
    query_time = time.time() - query_start
    
    # 2. Mesurer le temps de calcul des statistiques
    stats_start = time.time()
    
    if len(df) > 0:
        # Calculer les statistiques comme le fait le dashboard
        stats = df.groupby('variant').agg({
            'afreq': ['mean', 'std'],
            'coverage': 'mean',
            'norm_count': ['mean', 'std']
        })
    else:
        stats = None
    
    stats_time = time.time() - stats_start
    
    total_time = query_time + stats_time
    
    return {
        'sample_name': sample_name,
        'variant_count': len(df),
        'query_time_seconds': round(query_time, 4),
        'stats_calculation_time_seconds': round(stats_time, 4),
        'total_time_seconds': round(total_time, 4)
    }

def main():
    print("=" * 80)
    print("MESURE DES TEMPS DE CHARGEMENT - HD827 DATA")
    print("=" * 80)
    print(f"Début: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Connexion à la base de données
    print("Connexion à la base de données...")
    conn = pymysql.connect(**DB_CONFIG)
    print("✓ Connexion établie\n")
    
    # Chargement des configurations
    print("Chargement des configurations...")
    regions = read_regions()
    samples = read_cleared_samples()
    print(f"✓ {len(regions)} variants à surveiller")
    print(f"✓ {len(samples)} échantillons de référence\n")
    
    # Mesure des temps de chargement
    print("Mesure des temps de chargement par échantillon...")
    print("-" * 80)
    
    results = []
    total_start = time.time()
    
    for i, sample in enumerate(samples, 1):
        try:
            result = measure_sample_loading(conn, sample, regions)
            results.append(result)
            
            # Affichage de la progression
            print(f"[{i}/{len(samples)}] {sample[:50]:50s} | "
                  f"Variants: {result['variant_count']:3d} | "
                  f"Query: {result['query_time_seconds']:6.3f}s | "
                  f"Stats: {result['stats_calculation_time_seconds']:6.3f}s | "
                  f"Total: {result['total_time_seconds']:6.3f}s")
        except Exception as e:
            print(f"[{i}/{len(samples)}] {sample[:50]:50s} | ERREUR: {str(e)}")
            results.append({
                'sample_name': sample,
                'variant_count': 0,
                'query_time_seconds': 0,
                'stats_calculation_time_seconds': 0,
                'total_time_seconds': 0,
                'error': str(e)
            })
    
    total_elapsed = time.time() - total_start
    
    conn.close()
    
    # Calcul des statistiques globales
    print("\n" + "=" * 80)
    print("STATISTIQUES GLOBALES")
    print("=" * 80)
    
    df_results = pd.DataFrame(results)
    
    print(f"\nNombre total d'échantillons: {len(df_results)}")
    print(f"Temps total d'exécution: {total_elapsed:.2f} secondes")
    print(f"\nTemps de requête SQL:")
    print(f"  - Minimum: {df_results['query_time_seconds'].min():.4f}s")
    print(f"  - Maximum: {df_results['query_time_seconds'].max():.4f}s")
    print(f"  - Moyenne: {df_results['query_time_seconds'].mean():.4f}s")
    print(f"  - Médiane: {df_results['query_time_seconds'].median():.4f}s")
    
    print(f"\nTemps de calcul des statistiques:")
    print(f"  - Minimum: {df_results['stats_calculation_time_seconds'].min():.4f}s")
    print(f"  - Maximum: {df_results['stats_calculation_time_seconds'].max():.4f}s")
    print(f"  - Moyenne: {df_results['stats_calculation_time_seconds'].mean():.4f}s")
    print(f"  - Médiane: {df_results['stats_calculation_time_seconds'].median():.4f}s")
    
    print(f"\nTemps total par échantillon:")
    print(f"  - Minimum: {df_results['total_time_seconds'].min():.4f}s")
    print(f"  - Maximum: {df_results['total_time_seconds'].max():.4f}s")
    print(f"  - Moyenne: {df_results['total_time_seconds'].mean():.4f}s")
    print(f"  - Médiane: {df_results['total_time_seconds'].median():.4f}s")
    
    # Sauvegarde des résultats
    output_file = 'loading_times_HD827_comparison.csv'
    df_results.to_csv(output_file, index=False)
    
    print(f"\n✓ Résultats sauvegardés dans: {output_file}")
    print(f"\nFin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

if __name__ == "__main__":
    main()

