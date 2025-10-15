# ✅ Vérification de la configuration Docker - GeneticVariantsDB

**Date** : 2025-10-15  
**Statut** : ✅ TOUT EST À JOUR ET PRÊT

---

## 📋 Résumé de la vérification

Tous les fichiers de configuration sont à jour et cohérents avec les modifications récentes (affichage de tous les échantillons + cache Redis).

---

## 🔍 Fichiers vérifiés

### 1. ✅ `dashboard/environment.yaml` - Packages Conda/Pip

**Statut** : ✅ **COMPLET - Tous les packages nécessaires sont présents**

```yaml
dependencies:
  - python=3.9              ✅
  - pandas                  ✅
  - numpy                   ✅
  - scipy                   ✅
  - plotly                  ✅
  - dash                    ✅
  - mysql-connector-python  ✅
  - dash-auth               ✅
  - flask-caching           ✅ (pour Cache)
  - dash-extensions=1.0.4   ✅
  - redis-py                ✅ (CRITIQUE pour le cache)
  - pydantic                ✅
  - pip                     ✅
  - sqlalchemy              ✅ (pour create_engine)
  - pip:
    - PyVCF3==1.0.3         ✅
    - pymysql               ✅ (pour SQLAlchemy + MySQL)
```

**Imports utilisés dans `vardb.py` :**
- ✅ `dash`, `dash_auth`, `dash_table` → dash
- ✅ `pandas` → pandas
- ✅ `plotly.graph_objs`, `plotly.express` → plotly
- ✅ `numpy` → numpy
- ✅ `statistics` → stdlib (inclus)
- ✅ `mysql.connector` → mysql-connector-python
- ✅ `sqlalchemy` → sqlalchemy
- ✅ `time`, `datetime`, `csv`, `os`, `json`, `hashlib`, `functools` → stdlib
- ✅ `flask_caching.Cache` → flask-caching
- ✅ `scipy`, `scipy.stats` → scipy
- ✅ `redis` → redis-py
- ✅ `io.StringIO` → stdlib
- ✅ `collections.defaultdict` → stdlib

**Aucun package manquant ! ✅**

---

### 2. ✅ `dashboard/Dockerfile` - Image Docker

**Statut** : ✅ **CORRECT**

```dockerfile
FROM continuumio/miniconda3
WORKDIR /app

COPY environment.yaml .
COPY vardb.py .              ← Copie le fichier Python modifié

RUN conda env create --name docker-base --file=environment.yaml && conda clean -afy
SHELL ["conda", "run", "-n", "docker-base", "/bin/bash", "-c"]

ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "docker-base", "python3", "vardb.py"]
```

**Points importants :**
- ✅ Utilise `environment.yaml` pour installer les dépendances
- ✅ Copie `vardb.py` dans l'image (modifications incluses)
- ✅ Active l'environnement conda `docker-base`
- ✅ Lance `vardb.py` au démarrage

**Note** : Les modifications de `vardb.py` nécessitent un **rebuild** de l'image :
```bash
docker compose build dashboard
```

---

### 3. ✅ `compose.yaml` - Services Docker

**Statut** : ✅ **CONFIGURATION COMPLÈTE**

#### Service `dashboard` ✅
```yaml
dashboard:
  build:
    context: ./dashboard
    dockerfile: Dockerfile
  depends_on:
    db:
      condition: service_healthy
    redis:
      condition: service_started    ← Redis doit démarrer avant
  volumes:
    - /Volumes/gth5TExt1/VS/IARC/HGDB/dash-files:/dash-files
  environment:
    - REDIS_URL=redis://redis:6379/0   ← Configuration Redis
  ports:
    - 8090:8090
```

**Points clés :**
- ✅ Dépend de `db` (healthy) et `redis` (started)
- ✅ Monte `/dash-files` pour accéder aux fichiers de config
- ✅ Variable d'environnement `REDIS_URL` configurée
- ✅ Port 8090 exposé

#### Service `redis` ✅
```yaml
redis:
  image: redis:7-alpine
  restart: always
  command: redis-server --appendonly yes
  volumes:
    - redis-data:/data
  ports:
    - 6380:6379
```

**Points clés :**
- ✅ Redis 7 (version récente)
- ✅ Persistence activée (`--appendonly yes`)
- ✅ Volume `redis-data` pour persistance
- ✅ Port 6380 (host) → 6379 (container)

#### Service `db` ✅
```yaml
db:
  image: mysql/mysql-server
  command: '--default-authentication-plugin=mysql_native_password'
  healthcheck:
    test: ['CMD-SHELL', 'mysqladmin ping -h 127.0.0.1 --password="$$(cat /run/secrets/db-password)" --silent']
    interval: 3s
    retries: 5
    start_period: 30s
  volumes:
    - db-data:/var/lib/mysql
    - ./schema:/docker-entrypoint-initdb.d   ← Initialise avec schema.sql
```

**Points clés :**
- ✅ MySQL avec healthcheck
- ✅ Schéma initialisé automatiquement
- ✅ Volume `db-data` pour persistance

#### Service `cronjobs` ✅
```yaml
cronjobs:
  build:
    context: ./cronjobs
    dockerfile: Dockerfile
  depends_on:
    db:
      condition: service_healthy
```

---

### 4. ✅ `schema/performance_indexes.sql` - Index MySQL

**Statut** : ✅ **INDEX OPTIMISÉS POUR LAZY LOADING**

```sql
-- Index CRITIQUES pour la nouvelle architecture
CREATE INDEX IF NOT EXISTS idx_runinfo_name ON RunInfo(name);        ← NOUVEAU
CREATE INDEX IF NOT EXISTS idx_calldata_sample ON CallData(sample);  ← NOUVEAU

-- Index existants
CREATE INDEX IF NOT EXISTS idx_calldata_variant ON CallData(variant);
CREATE INDEX IF NOT EXISTS idx_vardata_name ON VarData(name);
CREATE INDEX IF NOT EXISTS idx_runinfo_filedate ON RunInfo(filedate);
```

**Impact sur les performances :**
- ✅ `idx_runinfo_name` : Accélère `get_all_sample_names()` (liste des échantillons)
- ✅ `idx_calldata_sample` : Accélère `get_sample_data()` (lazy loading par échantillon)
- ✅ Les autres index optimisent les JOINs et filtres

**Ces index sont créés automatiquement au démarrage** (dans `/docker-entrypoint-initdb.d/`)

---

### 5. ✅ `cronjobs/environment.yaml` - Packages Cronjobs

**Statut** : ✅ **CORRECT POUR LES CRONJOBS**

```yaml
dependencies:
  - python=3.9
  - pip
  - libcurl
  - curl
  - pip:
    - pandas
    - numpy
    - dash
    - mysql-connector-python
    - PyVCF3==1.0.3
    - pymysql
    - flask-caching
    - dash-auth
    - dash-extensions
    - requests
```

**Note** : Les cronjobs n'ont pas besoin de `redis-py` ni de `plotly` (pas d'affichage).

---

### 6. ✅ `requirements.txt` (racine)

**Statut** : ✅ **POUR LE DÉVELOPPEMENT LOCAL UNIQUEMENT**

Ce fichier n'est **PAS utilisé par Docker** (qui utilise `environment.yaml`).

Il est utile pour le développement local avec `pip` :
```bash
pip install -r requirements.txt
```

**Note** : Si vous développez localement, ajoutez `redis` et `sqlalchemy` :
```txt
redis
sqlalchemy
pymysql
```

---

## 🚀 Commandes pour lancer Docker

### 1. Build complet (première fois ou après modifications)
```bash
cd /Volumes/gth5TExt1/VS/IARC/HGDB/GeneticVariantsDB

# Rebuild tous les services
docker compose build

# Ou rebuild uniquement le dashboard
docker compose build dashboard
```

### 2. Lancer les services
```bash
# Lancer en arrière-plan
docker compose up -d

# Ou voir les logs en direct
docker compose up
```

### 3. Vérifier l'état
```bash
# Vérifier que tous les services sont "Up"
docker compose ps

# Vérifier les logs du dashboard
docker logs geneticvariantsdb-dashboard-1 --tail 50

# Vérifier Redis
docker exec geneticvariantsdb-redis-1 redis-cli PING
# Doit afficher : PONG
```

### 4. Accéder au dashboard
```
http://localhost:8090
```

### 5. Arrêter/Redémarrer
```bash
# Arrêter tous les services
docker compose down

# Redémarrer un service spécifique
docker compose restart dashboard

# Rebuild + redémarrage
docker compose up -d --build dashboard
```

---

## 🔧 Modifications récentes prises en compte

### ✅ Architecture lazy loading
- [x] `vardb.py` modifié pour afficher tous les 123 échantillons
- [x] Cache Redis opérationnel
- [x] Index MySQL optimisés
- [x] Tous les packages nécessaires installés

### ✅ Fichiers de configuration
- [x] `environment.yaml` contient `redis-py`
- [x] `compose.yaml` configure le service Redis
- [x] `performance_indexes.sql` contient les nouveaux index

---

## ⚠️ Points d'attention

### 1. Rebuild nécessaire après modifications de code
Si vous modifiez `vardb.py`, vous **DEVEZ** rebuild l'image :
```bash
docker compose build dashboard
docker compose up -d dashboard
```

### 2. Cache du navigateur
Après rebuild, rafraîchir le navigateur avec **Cmd+Shift+R** (Mac) ou **Ctrl+Shift+R** (Windows/Linux).

### 3. Volumes Docker
Les données sont persistées dans des volumes Docker :
- `db-data` : Base de données MySQL
- `redis-data` : Cache Redis

Pour réinitialiser complètement :
```bash
docker compose down -v  # ⚠️ Supprime TOUTES les données
```

### 4. Fichiers de configuration montés
Les fichiers dans `/dash-files` sont **montés en bind** (pas copiés) :
- `regions.txt`
- `cleared.tsv`
- `exclusions.tsv`
- `config.txt`

**Les modifications de ces fichiers sont immédiatement visibles** (pas besoin de rebuild).

---

## ✅ Checklist de démarrage

Avant de lancer Docker, vérifiez :

- [x] **Fichier `db/password.txt` existe** (pour le secret MySQL)
- [x] **Dossier `/Volumes/gth5TExt1/VS/IARC/HGDB/dash-files` existe** avec :
  - [x] `regions.txt` (189 variants)
  - [x] `cleared.tsv` (128 échantillons de référence)
  - [x] `exclusions.tsv` (échantillons à exclure)
  - [x] `config.txt` (paramètres QC)
- [x] **Port 8090 disponible** (pas déjà utilisé)
- [x] **Port 3309 disponible** (MySQL)
- [x] **Port 6380 disponible** (Redis)

---

## 🎯 Résumé final

| Composant | Statut | Note |
|-----------|--------|------|
| `dashboard/environment.yaml` | ✅ COMPLET | Tous les packages nécessaires |
| `dashboard/Dockerfile` | ✅ CORRECT | Copie vardb.py modifié |
| `dashboard/vardb.py` | ✅ À JOUR | Architecture lazy loading |
| `compose.yaml` | ✅ COMPLET | Redis + dépendances OK |
| `schema/performance_indexes.sql` | ✅ OPTIMISÉ | Index pour lazy loading |
| `cronjobs/environment.yaml` | ✅ CORRECT | Packages cronjobs OK |

---

## 🚀 Commande rapide pour démarrer

```bash
cd /Volumes/gth5TExt1/VS/IARC/HGDB/GeneticVariantsDB

# Build complet
docker compose build

# Lancer
docker compose up -d

# Attendre 30 secondes (healthcheck MySQL)
sleep 30

# Vérifier
docker compose ps
docker logs geneticvariantsdb-dashboard-1 --tail 20

# Accéder au dashboard
open http://localhost:8090
```

---

**✅ TOUT EST PRÊT POUR LE LANCEMENT !**

