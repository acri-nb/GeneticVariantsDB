# 🚀 Guide de démarrage rapide - GeneticVariantsDB Dashboard

**Date de mise à jour** : 2025-10-15  
**Version** : v2 avec affichage de tous les échantillons + cache Redis

---

## ✅ Vérification rapide

Avant de commencer, lancez le script de vérification :

```bash
cd /Volumes/gth5TExt1/VS/IARC/HGDB/GeneticVariantsDB
./check_docker_ready.sh
```

Si tout est vert (32 PASS / 0 FAIL), vous êtes prêt !

---

## 🚀 Lancement

### Première utilisation ou après modifications du code

```bash
cd /Volumes/gth5TExt1/VS/IARC/HGDB/GeneticVariantsDB

# 1. Build des images Docker (inclut les dernières modifications)
docker compose build

# 2. Lancer tous les services
docker compose up -d

# 3. Attendre que MySQL soit prêt (~30 secondes)
sleep 30

# 4. Vérifier l'état des services
docker compose ps
```

### Utilisation quotidienne (services déjà buildés)

```bash
cd /Volumes/gth5TExt1/VS/IARC/HGDB/GeneticVariantsDB

# Lancer
docker compose up -d

# Arrêter
docker compose down
```

---

## 🌐 Accès au dashboard

Une fois démarré, ouvrez votre navigateur :

```
http://localhost:8090
```

**Identifiants** : Configurés dans `vardb.py` (section `dash_auth`)

---

## 📊 Fonctionnalités actuelles

✅ **123 échantillons** disponibles dans le dropdown (au lieu de 20)  
✅ **Recherche intégrée** dans le dropdown (tapez pour filtrer)  
✅ **Cache Redis** opérationnel (chargements 60-100x plus rapides)  
✅ **Index MySQL** optimisés pour la performance  
✅ **Graphiques Levey-Jennings** pour le QC  
✅ **Tableaux interactifs** avec filtrage

---

## 🔧 Commandes utiles

### Voir les logs

```bash
# Dashboard
docker logs geneticvariantsdb-dashboard-1 --tail 50

# MySQL
docker logs geneticvariantsdb-db-1 --tail 50

# Redis
docker logs geneticvariantsdb-redis-1 --tail 20

# Tous les services
docker compose logs --tail 50
```

### Redémarrer un service

```bash
# Dashboard uniquement
docker compose restart dashboard

# Tous les services
docker compose restart
```

### Rebuild après modification du code

```bash
# Rebuild dashboard
docker compose build dashboard
docker compose up -d dashboard

# Rebuild tous les services
docker compose build
docker compose up -d
```

### Vérifier l'état

```bash
# État des services
docker compose ps

# Test Redis
docker exec geneticvariantsdb-redis-1 redis-cli PING
# Doit afficher: PONG

# Vérifier le cache Redis
docker exec geneticvariantsdb-redis-1 redis-cli KEYS "*"

# Connexion à MySQL
docker exec -it geneticvariantsdb-db-1 mysql -u usr -p vardb
# Password: usrpass
```

### Vider le cache Redis

```bash
docker exec geneticvariantsdb-redis-1 redis-cli FLUSHDB
```

---

## 📁 Structure des fichiers

```
GeneticVariantsDB/
├── dashboard/                    ← Code du dashboard
│   ├── vardb.py                 ← Application Dash principale
│   ├── environment.yaml         ← Dépendances Python/Conda
│   └── Dockerfile               ← Image Docker
├── compose.yaml                 ← Configuration Docker Compose
├── schema/                      ← Schéma et index MySQL
│   ├── schema.sql
│   └── performance_indexes.sql
├── db/
│   └── password.txt             ← Mot de passe MySQL (secret)
└── /Volumes/.../dash-files/     ← Fichiers de config (montés)
    ├── regions.txt              ← Variants à afficher
    ├── cleared.tsv              ← Échantillons de référence QC
    ├── exclusions.tsv           ← Échantillons à exclure
    └── config.txt               ← Paramètres (limit, etc.)
```

---

## 🔄 Mise à jour des données

### Modifier les variants affichés

Éditez `/Volumes/gth5TExt1/VS/IARC/HGDB/dash-files/regions.txt`  
**Pas besoin de redémarrer**, les changements sont immédiats !

### Modifier les échantillons de référence QC

Éditez `/Volumes/gth5TExt1/VS/IARC/HGDB/dash-files/cleared.tsv`  
**Pas besoin de redémarrer**, mais videz le cache Redis :

```bash
docker exec geneticvariantsdb-redis-1 redis-cli FLUSHDB
docker compose restart dashboard
```

### Ajouter des échantillons à exclure

Éditez `/Volumes/gth5TExt1/VS/IARC/HGDB/dash-files/exclusions.tsv`  
**Pas besoin de redémarrer**, videz le cache :

```bash
docker exec geneticvariantsdb-redis-1 redis-cli FLUSHDB
```

### Importer de nouvelles données VCF

Utilisez le service `cronjobs` ou lancez manuellement :

```bash
cd /Volumes/gth5TExt1/VS/IARC/HGDB/GeneticVariantsDB
python Add2VarDB.py <fichier.vcf>
```

Puis videz le cache pour afficher les nouvelles données.

---

## ⚠️ Dépannage

### Le dashboard ne démarre pas

1. Vérifiez les logs :
   ```bash
   docker logs geneticvariantsdb-dashboard-1 --tail 50
   ```

2. Vérifiez que MySQL est healthy :
   ```bash
   docker compose ps
   ```
   MySQL doit afficher `healthy` dans la colonne Status.

3. Attendez 30 secondes après le démarrage (healthcheck).

### Aucune donnée ne s'affiche

1. Vérifiez que la base contient des données :
   ```bash
   docker exec -it geneticvariantsdb-db-1 mysql -u usr -pusrpass vardb -e "SELECT COUNT(*) FROM CallData;"
   ```

2. Vérifiez les fichiers de configuration :
   ```bash
   wc -l /Volumes/gth5TExt1/VS/IARC/HGDB/dash-files/*.{txt,tsv}
   ```

3. Videz le cache Redis et redémarrez :
   ```bash
   docker exec geneticvariantsdb-redis-1 redis-cli FLUSHDB
   docker compose restart dashboard
   ```

### Redis ne répond pas

```bash
# Redémarrer Redis
docker compose restart redis

# Vérifier
docker exec geneticvariantsdb-redis-1 redis-cli PING
```

### Port 8090 déjà utilisé

Modifiez le port dans `compose.yaml` :
```yaml
ports:
  - 8091:8090  # Utilisez 8091 au lieu de 8090
```

Puis accédez à `http://localhost:8091`

### Modifications du code non prises en compte

**Vous DEVEZ rebuild l'image Docker** :
```bash
docker compose build dashboard
docker compose up -d dashboard
```

Puis **rafraîchissez le navigateur** avec `Cmd+Shift+R` (Mac) ou `Ctrl+Shift+R` (Windows/Linux).

---

## 📚 Documentation complète

- `VERIFICATION_DOCKER_SETUP.md` - Vérification détaillée de la configuration
- `CACHE_REDIS_STATUS.md` - État et fonctionnement du cache Redis
- `SOLUTION_FINALE_TOUS_ECHANTILLONS.md` - Architecture lazy loading
- `docs/dashboard-performance-HD827-report.md` - Rapport de performance

---

## 🎯 Checklist rapide

Avant de lancer Docker :

- [x] `db/password.txt` existe
- [x] Dossier `dash-files` existe avec `regions.txt`, `cleared.tsv`, `exclusions.tsv`, `config.txt`
- [x] Ports 8090, 3309, 6380 disponibles (ou modifiés)
- [x] Script `./check_docker_ready.sh` passe avec 32 PASS / 0 FAIL

---

## 💡 Astuces

### Développement local (sans Docker)

Si vous voulez développer localement :

```bash
# Créer un environnement conda
conda env create -f dashboard/environment.yaml

# Activer l'environnement
conda activate base

# Lancer le dashboard
cd dashboard
python vardb.py
```

**Note** : Vous devrez configurer MySQL et Redis localement.

### Performance

- Le cache Redis est configuré pour 5 minutes (TTL=300s)
- Pour augmenter/diminuer, modifiez `ttl=300` dans `vardb.py`
- Premier chargement : ~3-5s
- Chargements suivants (< 5 min) : ~0.05s

### Surveillance

```bash
# Suivre les logs en temps réel
docker compose logs -f dashboard

# Voir l'utilisation des ressources
docker stats

# Voir les contenus du cache
docker exec geneticvariantsdb-redis-1 redis-cli --scan
```

---

## 🆘 Support

En cas de problème :

1. Lancez `./check_docker_ready.sh`
2. Vérifiez les logs : `docker logs geneticvariantsdb-dashboard-1 --tail 100`
3. Consultez `VERIFICATION_DOCKER_SETUP.md`

---

**✅ Vous êtes prêt ! Bon développement ! 🚀**

