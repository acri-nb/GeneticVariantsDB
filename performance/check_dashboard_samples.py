#!/usr/bin/env python3
"""
Script pour vérifier quels échantillons sont visibles dans le dashboard
"""

import mysql.connector
import pandas as pd

# Connexion à la BD
conn = mysql.connector.connect(
    host='localhost',
    user='usr',
    password='usrpass',
    database='vardb',
    port=3306
)

print("="*80)
print("VÉRIFICATION DES ÉCHANTILLONS VISIBLES DANS LE DASHBOARD")
print("="*80)

# 1. Nombre total d'échantillons dans la BD
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM RunInfo")
total_samples = cursor.fetchone()[0]
print(f"\n📊 Total échantillons dans BD: {total_samples}")

# 2. Lire cleared.tsv
with open('/Volumes/gth5TExt1/VS/IARC/HGDB/dash-files/cleared.tsv', 'r') as f:
    cleared_samples = [line.strip() for line in f if line.strip()]

print(f"📊 Échantillons dans cleared.tsv: {len(cleared_samples)}")

# 3. Lire exclusions.tsv
try:
    with open('/Volumes/gth5TExt1/VS/IARC/HGDB/dash-files/exclusions.tsv', 'r') as f:
        exclusions = [line.strip() for line in f if line.strip()]
except:
    exclusions = []

print(f"📊 Échantillons exclus: {len(exclusions)}")

# 4. Simuler la requête du dashboard (from vardb.py get_sql function)
print("\n" + "="*80)
print("SIMULATION DE LA REQUÊTE DASHBOARD (get_sql)")
print("="*80)

# Lire regions.txt
with open('/Volumes/gth5TExt1/VS/IARC/HGDB/dash-files/regions.txt', 'r') as f:
    regions = [line.strip() for line in f if line.strip()]

print(f"\n📍 Variants dans regions.txt: {len(regions)}")

# Requête similaire à get_sql() dans vardb.py
query = """
SELECT DISTINCT r.name as sample_name
FROM CallData c
INNER JOIN VarData v ON v.id = c.variant
INNER JOIN RunInfo r ON r.id = c.sample
WHERE v.name IN ({})
ORDER BY r.name
""".format(','.join([f"'{region}'" for region in regions[:10]]))  # Tester avec 10 premiers

cursor.execute(query)
visible_samples = [row[0] for row in cursor.fetchall()]

print(f"\n✅ Échantillons visibles dans dashboard: {len(visible_samples)}")
print("\nPremiers 20 échantillons visibles:")
for i, sample in enumerate(visible_samples[:20], 1):
    in_cleared = "✓" if sample in cleared_samples else "✗"
    print(f"  {i:3d}. [{in_cleared}] {sample}")

# 5. Vérifier les échantillons de cleared.tsv qui ont des données
print("\n" + "="*80)
print("ÉCHANTILLONS DE cleared.tsv AVEC DONNÉES")
print("="*80)

cleared_with_data = []
cleared_without_data = []

for sample in cleared_samples:
    query = f"""
    SELECT COUNT(*) 
    FROM CallData c
    INNER JOIN VarData v ON v.id = c.variant
    INNER JOIN RunInfo r ON r.id = c.sample
    WHERE r.name = '{sample}'
    AND v.name IN ({','.join([f"'{region}'" for region in regions[:10]])})
    """
    cursor.execute(query)
    count = cursor.fetchone()[0]
    
    if count > 0:
        cleared_with_data.append((sample, count))
    else:
        cleared_without_data.append(sample)

print(f"\n✅ Avec données: {len(cleared_with_data)}/{len(cleared_samples)}")
print(f"❌ Sans données: {len(cleared_without_data)}/{len(cleared_samples)}")

if cleared_without_data:
    print("\n⚠️ Échantillons de cleared.tsv SANS données:")
    for sample in cleared_without_data[:10]:
        print(f"  • {sample}")
    if len(cleared_without_data) > 10:
        print(f"  ... et {len(cleared_without_data) - 10} autres")

# 6. Statistiques finales
print("\n" + "="*80)
print("RÉSUMÉ FINAL")
print("="*80)

print(f"""
📊 DONNÉES:
   • Total échantillons BD: {total_samples}
   • Échantillons visibles: {len(visible_samples)}
   • Échantillons cleared.tsv: {len(cleared_samples)}
   • Échantillons exclus: {len(exclusions)}

✅ STATUT:
   • Échantillons affichés dans dropdown: {len(visible_samples)}
   • Coverage cleared.tsv: {len(cleared_with_data)}/{len(cleared_samples)} ({100*len(cleared_with_data)/len(cleared_samples):.1f}%)
""")

if len(visible_samples) != total_samples:
    print(f"""
⚠️ ATTENTION:
   Seulement {len(visible_samples)}/{total_samples} échantillons sont visibles !
   
   Raisons possibles:
   1. Échantillons sans variants dans regions.txt
   2. Filtrage par exclusions.tsv
   3. Problème de requête dans get_sql()
""")
else:
    print("✅ Tous les échantillons sont potentiellement visibles")

cursor.close()
conn.close()

print("\n" + "="*80)

