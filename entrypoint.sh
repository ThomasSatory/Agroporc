#!/bin/bash
# Charger les variables d'environnement (cron ne les hérite pas)
set -a
source /app/.env
set +a

MODE="${1:-jour}"
echo "$(date '+%Y-%m-%d %H:%M') [cron] Lancement pipeline mode=$MODE"
cd /app && python main.py "$MODE"
echo "$(date '+%Y-%m-%d %H:%M') [cron] Terminé"
