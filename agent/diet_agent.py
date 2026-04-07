"""
Agent diététicien — appelle Claude via le CLI `claude -p` (auth OAuth gérée par Claude Code).
Pas besoin de clé API séparée.
"""
import json
import subprocess
import os
import shutil
from pathlib import Path

SPORT_PROFILE = os.getenv("SPORT_PROFILE", "sport régulier")
DAILY_CALORIES_TARGET = os.getenv("DAILY_CALORIES_TARGET", "2200")

CLAUDE_BIN = (
    shutil.which("claude")
    or "/Users/toam/.local/bin/claude"
)

PERSONNAGES_DIR = Path(__file__).parent.parent / "personnages"


def _load_personnages_desc() -> str:
    """Charge tous les personnages depuis les fichiers JSON et construit la description pour le prompt."""
    lines = []
    for f in sorted(PERSONNAGES_DIR.glob("*.json")):
        p = json.loads(f.read_text(encoding="utf-8"))
        lines.append(f"- **{p['prenom']}** {p['emoji']} — {p['role']}")
        lines.append(f"  Personnalité : {p['personnalite']}")
        lines.append(f"  Traits : {', '.join(p['traits'])}")
        lines.append(f"  Style : {p['style_de_parole']}")
        lines.append(f"  Sujets fétiches : {', '.join(p['sujets_fetiches'])}")
        lines.append(f"  Blagues récurrentes : {', '.join(p['blagues_recurrentes'])}")
        lines.append("")
    return "\n".join(lines)


def _build_system_prompt() -> str:
    """Construit le prompt système avec les personnages chargés dynamiquement."""
    personnages_desc = _load_personnages_desc()

    return f"""Tu es un expert en nutrition ET en gastronomie.
L'utilisateur pratique du sport régulièrement ({SPORT_PROFILE}) et suit ses macronutriments.
Son objectif calorique journalier est d'environ {DAILY_CALORIES_TARGET} kcal.

Pour chaque plat du jour soumis, tu dois fournir DEUX évaluations :

**Mode Sportif** : note selon l'adéquation nutritionnelle (ratio protéines, macros équilibrés, adapté au sportif).
**Mode Goulaf** : note selon le plaisir gustatif, la gourmandise, la générosité du plat, l'originalité. Un plat riche, savoureux et réconfortant sera bien noté en mode Goulaf même s'il est calorique.

Pour chaque plat :
1. Estimer la composition nutritionnelle approximative (protéines, glucides, lipides, calories)
2. Attribuer une note sportif (1-10) ET une note goulaf (1-10)
3. Justifier brièvement chaque note (2-3 phrases max chacune)
4. Désigner le plat recommandé pour chaque mode
5. Générer 2 à 4 faux commentaires humoristiques par plat (piochés parmi les personnages ci-dessous)

IMPORTANT : si le champ "plat" est une liste, cela signifie que le restaurant propose plusieurs options ce jour-là.
Dans ce cas, note chaque option séparément dans un tableau "options" au lieu des champs directs.

**Personnages pour les commentaires :**

{personnages_desc}

Chaque commentaire fait 1-2 phrases MAX. Le ton est décontracté, drôle, entre potes. Pas tous les personnages ne commentent chaque plat — choisis les 2-4 plus pertinents/drôles pour chaque plat. Varie les personnages d'un plat à l'autre.
Les personnages PEUVENT se répondre entre eux (ajoute un champ "reponse_a" avec le prénom du personnage auquel ils répondent). Maximum 1-2 réponses par plat.

Réponds UNIQUEMENT en JSON valide avec cette structure :
{{
  "plats": [
    {{
      "restaurant": "nom",
      "plat": "nom du plat unique",
      "prix": "prix",
      "nutrition_estimee": {{"calories": 0, "proteines_g": 0, "glucides_g": 0, "lipides_g": 0}},
      "note": 0,
      "justification": "texte sportif",
      "note_goulaf": 0,
      "justification_goulaf": "texte gourmand",
      "commentaires": [
        {{"auteur": "Prénom", "texte": "commentaire drôle"}},
        {{"auteur": "Prénom", "texte": "réponse", "reponse_a": "Prénom"}}
      ]
    }},
    {{
      "restaurant": "nom avec plusieurs options",
      "plat": ["option 1", "option 2"],
      "prix": "prix",
      "options": [
        {{
          "plat": "option 1",
          "nutrition_estimee": {{"calories": 0, "proteines_g": 0, "glucides_g": 0, "lipides_g": 0}},
          "note": 0,
          "justification": "texte sportif",
          "note_goulaf": 0,
          "justification_goulaf": "texte gourmand",
          "commentaires": [
            {{"auteur": "Prénom", "texte": "commentaire drôle"}}
          ]
        }}
      ]
    }}
  ],
  "recommandation": {{
    "restaurant": "nom du restaurant recommandé en mode sportif",
    "plat": "plat recommandé (option précise si plusieurs)",
    "raison": "explication courte mode sportif"
  }},
  "recommandation_goulaf": {{
    "restaurant": "nom du restaurant recommandé en mode goulaf",
    "plat": "plat recommandé (option précise si plusieurs)",
    "raison": "explication courte mode goulaf"
  }}
}}"""


def _get_oauth_token() -> str:
    """
    Lit le token OAuth de Claude Code depuis le macOS Keychain.
    Fallback sur ANTHROPIC_API_KEY si présente dans l'environnement.
    """
    # Fallback : clé API classique dans l'env
    env_key = os.getenv("ANTHROPIC_API_KEY", "")
    if env_key:
        return env_key

    # Lire le token OAuth depuis le Keychain macOS
    try:
        result = subprocess.run(
            ["security", "find-generic-password", "-l", "Claude Code-credentials", "-w"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            raw = result.stdout.strip()
            data = json.loads(raw)
            oauth = data.get("claudeAiOauth", {})
            token = oauth.get("accessToken", "")
            if token:
                return token
    except Exception as e:
        print(f"[diet_agent] Erreur lecture Keychain : {e}")

    raise ValueError(
        "Aucun token trouvé. Configurez ANTHROPIC_API_KEY dans .env "
        "ou assurez-vous d'être connecté à Claude Code."
    )


def evaluate_semaine(plats_par_jour: dict[str, list[dict]]) -> dict[str, dict]:
    """
    Évalue les plats de plusieurs jours en un seul appel Claude.

    Args:
        plats_par_jour: {"MARDI": [{"restaurant": ..., "plat": ..., "prix": ...}], ...}

    Returns:
        {"MARDI": {"plats": [...], "recommandation": {...}, "recommandation_goulaf": {...}}, ...}
    """
    if not plats_par_jour:
        return {}

    prompt = (
        f"{_build_system_prompt()}\n\n"
        f"Voici les plats du jour de PLUSIEURS jours de la semaine :\n\n"
        f"{json.dumps(plats_par_jour, ensure_ascii=False, indent=2)}\n\n"
        f"Pour CHAQUE jour, note chaque plat et donne ta recommandation.\n\n"
        f"Réponds en JSON avec cette structure :\n"
        f'{{\n'
        f'  "MARDI": {{\n'
        f'    "plats": [{{"restaurant": "...", "plat": "...", "prix": "...", "nutrition_estimee": {{...}}, "note": 0, "justification": "...", "note_goulaf": 0, "justification_goulaf": "...", "commentaires": [...]}}],\n'
        f'    "recommandation": {{"restaurant": "...", "plat": "...", "raison": "..."}},\n'
        f'    "recommandation_goulaf": {{"restaurant": "...", "plat": "...", "raison": "..."}}\n'
        f'  }},\n'
        f'  ...\n'
        f'}}'
    )

    result = subprocess.run(
        [CLAUDE_BIN, "-p", prompt, "--output-format", "text"],
        capture_output=True, text=True, timeout=120,
    )

    if result.returncode != 0:
        raise RuntimeError(f"claude CLI error: {result.stderr.strip()}")

    raw = result.stdout.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def evaluate(plats: list[dict]) -> dict:
    """
    Évalue les plats via `claude -p` (CLI Claude Code, auth OAuth intégrée).

    Args:
        plats: liste de dicts { restaurant, plat, prix }

    Returns:
        dict avec notes et recommandation
    """
    prompt = (
        f"{_build_system_prompt()}\n\n"
        f"Voici les plats du jour disponibles aujourd'hui :\n\n"
        f"{json.dumps(plats, ensure_ascii=False, indent=2)}\n\n"
        f"Note chaque plat et dis-moi lequel manger."
    )

    result = subprocess.run(
        [CLAUDE_BIN, "-p", prompt, "--output-format", "text"],
        capture_output=True, text=True, timeout=60,
    )

    if result.returncode != 0:
        raise RuntimeError(f"claude CLI error: {result.stderr.strip()}")

    raw = result.stdout.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def evaluate_image(image_url: str, context: str = "") -> str:
    """
    Utilise Claude Vision pour extraire le texte d'une photo de menu.

    Args:
        image_url: URL de l'image du menu
        context: contexte additionnel

    Returns:
        texte extrait décrivant le plat
    """
    token = _get_oauth_token()
    client = anthropic.Anthropic(api_key=token)

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {"type": "url", "url": image_url},
                },
                {
                    "type": "text",
                    "text": (
                        "C'est une photo du plat du jour d'un restaurant. "
                        "Extrait le nom du plat et le prix si visible. "
                        "Réponds en une seule ligne : 'NOM DU PLAT - PRIX€' "
                        "ou juste 'NOM DU PLAT' si pas de prix visible. "
                        f"{context}"
                    )
                }
            ],
        }],
    )
    return message.content[0].text.strip()
