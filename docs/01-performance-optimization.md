# Performance Optimization Guide

## Étape 1: Index de Base de Données

### Objectif
Améliorer les performances des requêtes en ajoutant des index stratégiques sur les tables les plus sollicitées.

### Index Créés

#### Table CallData (critique)
- `idx_calldata_sample`: Index sur la colonne `sample`
- `idx_calldata_variant`: Index sur la colonne `variant` 
- `idx_calldata_variant_sample`: Index composite sur `(variant, sample)`

#### Table VarData
- `idx_vardata_gene`: Index sur la colonne `gene`
- `idx_vardata_name`: Index sur la colonne `name`
- `idx_vardata_hgvs`: Index sur la colonne `hgvs`

#### Table RunInfo
- `idx_runinfo_filedate`: Index sur la colonne `filedate`
- `idx_runinfo_name`: Index sur la colonne `name`

### Application des Index

1. **Démarrer les services:**
```bash
docker-compose up -d
```

2. **Appliquer les index:**
```bash
docker exec -i $(docker-compose ps -q db) mysql -u root -p$(cat db/password.txt) vardb < schema/performance_indexes.sql
```

3. **Vérifier l'application:**
```bash
docker exec -i $(docker-compose ps -q db) mysql -u root -p$(cat db/password.txt) vardb -e "SHOW INDEX FROM CallData;"
```

### Impact Attendu
- Réduction de 70-80% du temps d'exécution des requêtes JOIN
- Amélioration significative du temps de chargement initial
- Meilleure réactivité lors du changement d'échantillon

### Test de Performance
Avant/après l'application des index, mesurer:
- Temps de chargement initial de l'application
- Temps de réponse lors du changement d'échantillon dans le dropdown
- Temps de génération des graphiques Levey-Jennings