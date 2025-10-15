#!/bin/bash
# Script de vérification rapide - Configuration Docker GeneticVariantsDB
# Usage: ./check_docker_ready.sh

echo "═══════════════════════════════════════════════════════════"
echo "🔍 Vérification de la configuration Docker"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Compteurs
PASS=0
FAIL=0

# Fonction de vérification
check() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ PASS${NC} - $2"
        ((PASS++))
    else
        echo -e "${RED}❌ FAIL${NC} - $2"
        ((FAIL++))
    fi
}

# 1. Vérifier Docker
echo "━━━ 1. Docker ━━━"
docker --version > /dev/null 2>&1
check $? "Docker installé"

docker compose version > /dev/null 2>&1
check $? "Docker Compose installé"
echo ""

# 2. Vérifier fichiers de configuration
echo "━━━ 2. Fichiers de configuration ━━━"

[ -f "db/password.txt" ]
check $? "db/password.txt existe"

[ -f "dashboard/environment.yaml" ]
check $? "dashboard/environment.yaml existe"

[ -f "dashboard/Dockerfile" ]
check $? "dashboard/Dockerfile existe"

[ -f "dashboard/vardb.py" ]
check $? "dashboard/vardb.py existe"

[ -f "compose.yaml" ]
check $? "compose.yaml existe"

[ -f "schema/performance_indexes.sql" ]
check $? "schema/performance_indexes.sql existe"
echo ""

# 3. Vérifier dash-files
echo "━━━ 3. Fichiers dash-files ━━━"
DASH_FILES_DIR="/Volumes/gth5TExt1/VS/IARC/HGDB/dash-files"

[ -d "$DASH_FILES_DIR" ]
check $? "Dossier dash-files existe"

[ -f "$DASH_FILES_DIR/regions.txt" ]
check $? "regions.txt existe"

[ -f "$DASH_FILES_DIR/cleared.tsv" ]
check $? "cleared.tsv existe"

[ -f "$DASH_FILES_DIR/exclusions.tsv" ]
check $? "exclusions.tsv existe"

[ -f "$DASH_FILES_DIR/config.txt" ]
check $? "config.txt existe"
echo ""

# 4. Vérifier packages dans environment.yaml
echo "━━━ 4. Packages critiques dans environment.yaml ━━━"

grep -q "redis-py" dashboard/environment.yaml
check $? "redis-py présent (CRITIQUE pour cache)"

grep -q "sqlalchemy" dashboard/environment.yaml
check $? "sqlalchemy présent"

grep -q "pymysql" dashboard/environment.yaml
check $? "pymysql présent"

grep -q "flask-caching" dashboard/environment.yaml
check $? "flask-caching présent"
echo ""

# 5. Vérifier compose.yaml
echo "━━━ 5. Configuration Docker Compose ━━━"

grep -q "redis:" compose.yaml
check $? "Service Redis défini"

grep -q "REDIS_URL" compose.yaml
check $? "Variable REDIS_URL configurée"

grep -q "redis:7-alpine" compose.yaml
check $? "Redis version 7 spécifiée"

grep -q "condition: service_healthy" compose.yaml
check $? "Healthcheck MySQL configuré"
echo ""

# 6. Vérifier index MySQL
echo "━━━ 6. Index MySQL pour lazy loading ━━━"

grep -q "idx_runinfo_name" schema/performance_indexes.sql
check $? "Index idx_runinfo_name (liste échantillons)"

grep -q "idx_calldata_sample" schema/performance_indexes.sql
check $? "Index idx_calldata_sample (lazy loading)"
echo ""

# 7. Vérifier l'état des services Docker
echo "━━━ 7. Services Docker ━━━"

docker compose ps > /dev/null 2>&1
if [ $? -eq 0 ]; then
    # Services existent, vérifier leur état
    RUNNING=$(docker compose ps | grep -c "Up")
    if [ $RUNNING -ge 3 ]; then
        check 0 "Services Docker en cours d'exécution ($RUNNING services)"
        
        # Vérifier chaque service
        docker compose ps | grep -q "dashboard.*Up"
        check $? "Service dashboard en cours d'exécution"
        
        docker compose ps | grep -q "db.*Up.*healthy"
        check $? "Service db en cours d'exécution (healthy)"
        
        docker compose ps | grep -q "redis.*Up"
        check $? "Service redis en cours d'exécution"
    else
        check 1 "Services Docker ne sont pas tous démarrés"
    fi
else
    echo -e "${YELLOW}⚠️  INFO${NC} - Services Docker non démarrés (normal si pas encore lancés)"
fi
echo ""

# 8. Vérifier Redis si les services tournent
if docker compose ps | grep -q "redis.*Up"; then
    echo "━━━ 8. Test Redis ━━━"
    docker exec geneticvariantsdb-redis-1 redis-cli PING > /dev/null 2>&1
    check $? "Redis répond au PING"
    
    KEYS=$(docker exec geneticvariantsdb-redis-1 redis-cli KEYS "*" 2>/dev/null | wc -l)
    if [ $KEYS -gt 0 ]; then
        echo -e "${GREEN}✅ INFO${NC} - Cache Redis contient $KEYS clé(s)"
    else
        echo -e "${YELLOW}⚠️  INFO${NC} - Cache Redis vide (normal au premier démarrage)"
    fi
    echo ""
fi

# 9. Vérifier vardb.py (modifications lazy loading)
echo "━━━ 9. Modifications lazy loading dans vardb.py ━━━"

grep -q "def get_db_connection" dashboard/vardb.py
check $? "Fonction get_db_connection() présente"

grep -q "redis_py" dashboard/vardb.py || grep -q "import redis" dashboard/vardb.py
check $? "Import redis présent"

grep -q "cache_get\|cache_set" dashboard/vardb.py
check $? "Fonctions de cache présentes"

# Vérifier que la limite de 20 a été supprimée du DROPDOWN (pas des graphiques LJ)
# La ligne correcte doit être : options = [{'label': i, 'value': i} for i in unique_samples]
if grep -A 15 "def make_drpdown" dashboard/vardb.py | grep -q "for i in unique_samples"; then
    check 0 "Dropdown affiche TOUS les échantillons (pas de limite)"
else
    check 1 "Dropdown limité à 20 échantillons"
fi

# Note: Les graphiques Levey-Jennings gardent [-20:] pour la lisibilité (normal)
echo ""

# Résumé
echo "═══════════════════════════════════════════════════════════"
echo -e "📊 Résumé: ${GREEN}$PASS PASS${NC} | ${RED}$FAIL FAIL${NC}"
echo "═══════════════════════════════════════════════════════════"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✅ TOUT EST PRÊT !${NC} Vous pouvez lancer Docker :"
    echo ""
    echo "   docker compose build"
    echo "   docker compose up -d"
    echo ""
    echo "   Dashboard: http://localhost:8090"
    exit 0
else
    echo -e "${RED}❌ PROBLÈMES DÉTECTÉS${NC} ($FAIL)"
    echo ""
    echo "Consultez VERIFICATION_DOCKER_SETUP.md pour plus de détails."
    exit 1
fi

