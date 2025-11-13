# Étape 2: Implémentation du Cache Redis

## Objectif
Ajouter un système de cache Redis pour réduire drastiquement les temps de chargement en évitant les requêtes répétitives à la base de données.

## Modifications Apportées

### 1. Docker Compose (`compose.yaml`)
- Ajout du service Redis avec persistance
- Configuration des dépendances pour le dashboard
- Variable d'environnement `REDIS_URL`

### 2. Environment Conda (`dashboard/environment.yaml`)
- Ajout de `redis-py` pour la connexion Redis

### 3. Code Python Optimisé (`dashboard/vardb_optimized.py`)
- Implémentation du cache Redis avec TTL (5 minutes)
- Requête SQL optimisée avec JOIN explicites
- Filtre temporel (dernière année seulement)
- Fonction de cache pour `getSummary()`

## Fonctionnalités du Cache

### Cache Principal
- **Clé**: Hash MD5 des paramètres de requête
- **TTL**: 5 minutes (300 secondes)
- **Données**: DataFrame principal de variants

### Cache Secondaire
- **Clé**: Hash incluant le type biomoléculaire (DNA/RNA)
- **TTL**: 5 minutes
- **Données**: Résultats des fonctions `getSummary()`

### Optimisations SQL
```sql
-- Requête optimisée avec JOIN explicites
SELECT c.pass_filter, c.afreq, c.coverage, c.norm_count, c.sample,
       v.name, r.IonWF_version, r.name, r.filedate,
       t.name, h.transcript, h.HGVSc, h.HGVSp, g.name
FROM CallData c
INNER JOIN VarData v ON v.id = c.variant
INNER JOIN RunInfo r ON r.id = c.sample
WHERE r.filedate >= (SELECT MAX(filedate) - 365 FROM RunInfo)
ORDER BY r.filedate DESC, v.name
```

## Déploiement

### 1. Arrêter les services existants
```bash
docker compose down
```

### 2. Reconstruire avec Redis
```bash
docker compose build
docker compose up -d
```

### 3. Vérifier Redis
```bash
docker exec -it geneticvariantsdb-redis-1 redis-cli ping
```

### 4. Tester l'application
- Premier chargement: ~10-15 secondes (cache miss)
- Chargements suivants: ~1-2 secondes (cache hit)

## Monitoring du Cache

### Statistiques Redis
```bash
docker exec -it geneticvariantsdb-redis-1 redis-cli info stats
```

### Vider le cache (si nécessaire)
```bash
docker exec -it geneticvariantsdb-redis-1 redis-cli flushdb
```

## Impact Attendu
- **Réduction des temps de chargement**: 80-90%
- **Diminution de la charge DB**: 70-80%
- **Amélioration de l'expérience utilisateur**: Significative

## Notes Importantes
- Le cache se vide automatiquement après 5 minutes
- Les données fraîches sont récupérées lors du premier accès post-expiration
- Redis persiste les données sur disque pour la récupération après redémarrage