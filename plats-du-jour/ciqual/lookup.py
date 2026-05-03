"""
Lookup d'ingrédients dans la table Ciqual.

Charge `ciqual_index.json` au premier appel (cache process-local) puis expose :
- find(query)               -> meilleur match unique (heuristique stricte)
- find_candidates(query, k) -> top-K candidats (matcheur permissif, pour LLM picker)
- get_entry_by_code(code)   -> entrée brute par code Ciqual
- compute_macros(items)     -> agrège (kcal, prot, gluc, lip) avec fuzzy match
- compute_macros_from_codes(items_with_codes) -> agrège quand un code Ciqual
                            a déjà été choisi explicitement (par le LLM picker)

Le matching textuel est volontairement simple : normalisation FR (lowercase,
sans accents, sans ponctuation), stemming basique pluriel/accord, scoring par
tokens. Le bon match exact est typiquement choisi par le LLM picker à partir
des candidats permissifs ; cette logique reste comme garde-fou.
"""
from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import TypedDict

INDEX_PATH = Path(__file__).parent / "ciqual_index.json"

# Mots vides FR qu'on ignore lors du scoring
# /!\ NE PAS y mettre "cuit/cru" : ça change ~50% des kcal sur les féculents.
STOPWORDS = {
    "de", "du", "des", "le", "la", "les", "l", "d", "a", "au", "aux",
    "en", "et", "ou", "un", "une", "sans", "avec", "ajoute", "sel",
}

# Suffixes français retirés pour normaliser pluriel/accord. Ordre important.
_SUFFIXES = ("aux", "eaux", "es", "er", "s", "x", "e")


def _stem(t: str) -> str:
    """Stemmer FR très simple : pluriels et accords. Min 3 chars conservés."""
    for suf in _SUFFIXES:
        if t.endswith(suf) and len(t) - len(suf) >= 3:
            return t[: -len(suf)]
    return t


def _matches_token(a: str, b: str) -> bool:
    """Match exact après stemming (les variantes ont déjà été stemmées en amont)."""
    return a == b


class CiqualEntry(TypedDict):
    code: str
    nom: str
    grp: str
    kcal: float | None
    prot: float | None
    gluc: float | None
    lip: float | None


class IngredientItem(TypedDict):
    nom: str
    grammes: float


class IngredientResolved(TypedDict):
    nom_query: str
    grammes: float
    matched_nom: str | None
    matched_code: str | None
    kcal: float
    prot: float
    gluc: float
    lip: float


def _normalize(s: str) -> str:
    s = s.lower().strip()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _tokens(s: str) -> list[str]:
    """Tokens stemmés, dans l'ordre, sans stopwords ni doublons (1ère occurrence gardée)."""
    seen: set[str] = set()
    out: list[str] = []
    for t in _normalize(s).split():
        if not t or t in STOPWORDS:
            continue
        st = _stem(t)
        if st in seen:
            continue
        seen.add(st)
        out.append(st)
    return out


@lru_cache(maxsize=1)
def _index() -> list[tuple[CiqualEntry, list[str], set[str], bool]]:
    """(entry, tokens_in_order, tokens_set, is_aliment_moyen)"""
    raw: list[CiqualEntry] = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    out = []
    for e in raw:
        toks = _tokens(e["nom"])
        is_avg = "aliment moyen" in e["nom"].lower()
        out.append((e, toks, set(toks), is_avg))
    return out


def find(query: str) -> CiqualEntry | None:
    """Renvoie l'entrée Ciqual la plus proche, ou None si rien de pertinent.

    Heuristiques :
    - Le 1er token de la query (le nom de l'aliment) doit être dans les 2
      premiers tokens de l'entrée. Filtre fort qui élimine les "Jambon de
      poulet" / "Sel blanc alimentaire" quand on cherche "poulet" / "blanc".
    - Bonus de +0.5 si le head est en position 0 (préférer les entrées dont
      l'aliment principal correspond exactement).
    - Bonus de +0.5 pour les entrées "aliment moyen" mais seulement quand la
      query est courte (≤ 2 tokens). Sinon ces entrées génériques captureraient
      à tort les requêtes spécifiques.
    """
    q_tokens = _tokens(query)
    if not q_tokens:
        return None

    head_token = q_tokens[0]
    q_set = set(q_tokens)
    bare_query = len(q_tokens) == 1  # "Pomme", "Beurre" — privilégie l'aliment moyen
    best: tuple[float, CiqualEntry] | None = None
    for entry, e_tokens_list, e_set, is_avg in _index():
        if not e_tokens_list:
            continue
        head_idx = next(
            (i for i, t in enumerate(e_tokens_list[:2]) if t == head_token),
            -1,
        )
        if head_idx < 0:
            continue

        matched_weight = 2.0  # head match
        for qt in q_tokens[1:]:
            if qt in e_set:
                matched_weight += 1.0
        extra = max(0, len(e_set) - len(q_set))
        score = matched_weight - 0.10 * extra
        if head_idx == 0:
            score += 0.5
        if is_avg and bare_query:
            score += 1.0
        if best is None or score > best[0]:
            best = (score, entry)

    if best is None or best[0] < 1.5:
        return None
    return best[1]


def find_candidates(query: str, k: int = 8) -> list[CiqualEntry]:
    """Top-K candidats Ciqual triés par score, filtrage permissif.

    Différences avec `find()` :
    - Le head token peut être dans les 3 premiers tokens de l'entrée (vs 2),
      ce qui laisse passer "Frites de pommes de terre" pour la query "pomme".
    - Aucun seuil minimal de score (on renvoie même les matches faibles).
    - Renvoie une liste triée score décroissant ; le LLM picker fait le tri
      sémantique en aval.

    Cette fonction est faite pour alimenter le picker LLM en candidats : on
    privilégie le rappel à la précision.
    """
    q_tokens = _tokens(query)
    if not q_tokens:
        return []

    head_token = q_tokens[0]
    q_set = set(q_tokens)
    bare_query = len(q_tokens) == 1
    scored: list[tuple[float, CiqualEntry]] = []
    for entry, e_tokens_list, e_set, is_avg in _index():
        if not e_tokens_list:
            continue
        head_idx = next(
            (i for i, t in enumerate(e_tokens_list[:3]) if t == head_token),
            -1,
        )
        if head_idx < 0:
            continue

        matched_weight = 2.0
        for qt in q_tokens[1:]:
            if qt in e_set:
                matched_weight += 1.0
        extra = max(0, len(e_set) - len(q_set))
        score = matched_weight - 0.10 * extra
        if head_idx == 0:
            score += 0.5
        if is_avg and bare_query:
            score += 1.0
        scored.append((score, entry))

    scored.sort(key=lambda x: -x[0])
    return [e for _, e in scored[:k]]


def get_entry_by_code(code: str) -> CiqualEntry | None:
    """Renvoie l'entrée Ciqual par son code, ou None si inconnu."""
    code = (code or "").strip()
    if not code:
        return None
    for entry, _, _, _ in _index():
        if entry["code"] == code:
            return entry
    return None


def compute_macros(items: list[IngredientItem]) -> tuple[dict[str, float], list[IngredientResolved], float]:
    """
    Agrège les macros pour une liste d'ingrédients.

    Returns:
        (totaux, détail_par_ingrédient, ratio_masse_non_matchée)
        totaux = {calories, proteines_g, glucides_g, lipides_g} arrondis
        ratio_masse_non_matchée ∈ [0, 1] — sert à décider si on fallback
    """
    totals = {"calories": 0.0, "proteines_g": 0.0, "glucides_g": 0.0, "lipides_g": 0.0}
    detail: list[IngredientResolved] = []
    masse_totale = 0.0
    masse_non_matchee = 0.0

    for item in items:
        nom = item.get("nom", "").strip()
        try:
            grammes = float(item.get("grammes", 0) or 0)
        except (TypeError, ValueError):
            grammes = 0.0
        if grammes <= 0 or not nom:
            continue
        masse_totale += grammes
        entry = find(nom)
        if entry is None:
            masse_non_matchee += grammes
            detail.append({
                "nom_query": nom, "grammes": grammes,
                "matched_nom": None, "matched_code": None,
                "kcal": 0.0, "prot": 0.0, "gluc": 0.0, "lip": 0.0,
            })
            continue

        factor = grammes / 100.0
        kcal = (entry["kcal"] or 0.0) * factor
        prot = (entry["prot"] or 0.0) * factor
        gluc = (entry["gluc"] or 0.0) * factor
        lip = (entry["lip"] or 0.0) * factor

        totals["calories"] += kcal
        totals["proteines_g"] += prot
        totals["glucides_g"] += gluc
        totals["lipides_g"] += lip

        detail.append({
            "nom_query": nom, "grammes": grammes,
            "matched_nom": entry["nom"], "matched_code": entry["code"],
            "kcal": round(kcal, 1), "prot": round(prot, 1),
            "gluc": round(gluc, 1), "lip": round(lip, 1),
        })

    rounded = {
        "calories": round(totals["calories"]),
        "proteines_g": round(totals["proteines_g"], 1),
        "glucides_g": round(totals["glucides_g"], 1),
        "lipides_g": round(totals["lipides_g"], 1),
    }
    ratio_unmatched = (masse_non_matchee / masse_totale) if masse_totale > 0 else 1.0
    return rounded, detail, ratio_unmatched


def compute_macros_from_codes(
    items: list[dict],
) -> tuple[dict[str, float], list[IngredientResolved], float]:
    """Agrège les macros à partir d'items ayant déjà un code Ciqual choisi.

    Args:
        items: [{nom, grammes, code: str | None}]
            - Si `code` est fourni et valide, on l'utilise (calcul déterministe).
            - Sinon on retombe sur un fuzzy `find()` (meilleur effort).

    Returns: (totaux, détail, ratio_masse_non_matchée), même format que compute_macros.
    """
    totals = {"calories": 0.0, "proteines_g": 0.0, "glucides_g": 0.0, "lipides_g": 0.0}
    detail: list[IngredientResolved] = []
    masse_totale = 0.0
    masse_non_matchee = 0.0

    for item in items:
        nom = (item.get("nom") or "").strip()
        try:
            grammes = float(item.get("grammes", 0) or 0)
        except (TypeError, ValueError):
            grammes = 0.0
        if grammes <= 0 or not nom:
            continue
        masse_totale += grammes

        entry: CiqualEntry | None = None
        code = item.get("code")
        if code:
            entry = get_entry_by_code(code)
        if entry is None:
            entry = find(nom)

        if entry is None:
            masse_non_matchee += grammes
            detail.append({
                "nom_query": nom, "grammes": grammes,
                "matched_nom": None, "matched_code": None,
                "kcal": 0.0, "prot": 0.0, "gluc": 0.0, "lip": 0.0,
            })
            continue

        factor = grammes / 100.0
        kcal = (entry["kcal"] or 0.0) * factor
        prot = (entry["prot"] or 0.0) * factor
        gluc = (entry["gluc"] or 0.0) * factor
        lip = (entry["lip"] or 0.0) * factor

        totals["calories"] += kcal
        totals["proteines_g"] += prot
        totals["glucides_g"] += gluc
        totals["lipides_g"] += lip

        detail.append({
            "nom_query": nom, "grammes": grammes,
            "matched_nom": entry["nom"], "matched_code": entry["code"],
            "kcal": round(kcal, 1), "prot": round(prot, 1),
            "gluc": round(gluc, 1), "lip": round(lip, 1),
        })

    rounded = {
        "calories": round(totals["calories"]),
        "proteines_g": round(totals["proteines_g"], 1),
        "glucides_g": round(totals["glucides_g"], 1),
        "lipides_g": round(totals["lipides_g"], 1),
    }
    ratio_unmatched = (masse_non_matchee / masse_totale) if masse_totale > 0 else 1.0
    return rounded, detail, ratio_unmatched
