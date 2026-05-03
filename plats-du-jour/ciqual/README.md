# Intégration table Ciqual

Source : https://ciqual.anses.fr/ (table de composition nutritionnelle ANSES, version 2025_11_03 utilisée).

## Pourquoi

Avant, `diet_agent` demandait à Claude d'estimer directement les macros (calories, protéines, glucides, lipides) à partir du nom du plat. C'était une estimation pure LLM, à ±20-30 % près.

Maintenant on procède en deux étapes :
1. Le LLM **décompose le plat en ingrédients + grammages** (format canonique style Ciqual : "Poulet, blanc, grillé", "Riz blanc, cuit", …).
2. On agrège les macros via la **table Ciqual** (mesures de labo) côté Python.

La part "imaginaire" est limitée à l'estimation des grammages d'une portion. Les valeurs nutritionnelles par 100 g sont mesurées.

## Fichiers

- `data/*.xml` (gitignore) — les 5 XML bruts téléchargés depuis l'ANSES (~65 Mo)
- `ciqual_index.json` — index slim ne gardant que les macros utiles (~430 ko, versionné)
- `build_index.py` — parse les XML et régénère le JSON
- `lookup.py` — module utilisé par `diet_agent` : `find(query)` + `compute_macros(items)`

## Mise à jour

Quand l'ANSES publie une nouvelle version :
1. Télécharger les 5 XML depuis https://ciqual.anses.fr/ (onglet "Téléchargement")
2. Les placer dans `data/`
3. Lancer `python -m ciqual.build_index` (depuis `plats-du-jour/`)
4. Commit le nouveau `ciqual_index.json`

## Comportement de fallback

Si plus de 30 % de la masse d'ingrédients d'un plat n'est pas matchée dans la table (ex. plat très inhabituel ou mal décomposé), on retombe sur l'estimation LLM directe (`nutrition_estimee_llm`). Le seuil est dans `agent/diet_agent.py` (`UNMATCHED_FALLBACK_THRESHOLD`).

Le champ `nutrition_source` (`"ciqual"` ou `"llm"`) sur chaque plat indique laquelle a été retenue.
