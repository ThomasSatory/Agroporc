"""
Création interactive d'un nouveau personnage IA.

Usage : python main.py nouveau-personnage
    ou : python creer_personnage.py

Demande tous les champs nécessaires, écrit le JSON dans personnages/,
et ajoute la ligne correspondante dans lib/characters.ts.
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

PERSONNAGES_DIR = Path(__file__).parent / "personnages"
CHARACTERS_TS = Path(__file__).parent.parent / "lib" / "characters.ts"


def _slug(prenom: str) -> str:
    s = unicodedata.normalize("NFKD", prenom).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "_", s).strip("_").lower()
    return s


def _ask(label: str, *, required: bool = True, multiline: bool = False, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    if multiline:
        print(f"{label}{suffix} (termine par une ligne vide) :")
        lines = []
        while True:
            try:
                line = input()
            except EOFError:
                break
            if line == "":
                break
            lines.append(line)
        value = "\n".join(lines).strip()
    else:
        value = input(f"{label}{suffix} : ").strip()

    if not value and default is not None:
        return default
    if not value and required:
        print("  → champ obligatoire, réessaie.")
        return _ask(label, required=required, multiline=multiline, default=default)
    return value


def _ask_list(label: str) -> list[str]:
    print(f"{label} (une entrée par ligne, ligne vide pour terminer) :")
    items = []
    while True:
        try:
            line = input(f"  {len(items) + 1}. ").strip()
        except EOFError:
            break
        if not line:
            break
        items.append(line)
    return items


def _update_characters_ts(prenom: str, couleur: str, emoji: str, image: str | None) -> bool:
    if not CHARACTERS_TS.exists():
        print(f"[!] {CHARACTERS_TS} introuvable, skip mise à jour frontend.")
        return False
    content = CHARACTERS_TS.read_text(encoding="utf-8")

    if re.search(rf'name:\s*"{re.escape(prenom)}"', content):
        print(f"[=] {prenom} déjà présent dans characters.ts, pas d'ajout.")
        return False

    fields = [f'name: "{prenom}"', f'color: "{couleur}"', f'emoji: "{emoji}"']
    if image:
        fields.append(f'image: "{image}"')
    new_line = f"  {{ {', '.join(fields)} }},\n"

    pattern = re.compile(r"(export const CHARACTERS: Character\[\] = \[\n)((?:.*\n)*?)(\];\n)", re.MULTILINE)
    m = pattern.search(content)
    if not m:
        print("[!] Structure de characters.ts non reconnue, ajoute la ligne à la main :")
        print(new_line.rstrip())
        return False

    updated = content[: m.end(2)] + new_line + content[m.end(2) :]
    CHARACTERS_TS.write_text(updated, encoding="utf-8")
    return True


def creer_personnage() -> None:
    print("── Nouveau personnage IA ──\n")

    prenom = _ask("Prénom (ex: Nova)")
    slug = _slug(prenom)
    path = PERSONNAGES_DIR / f"{slug}.json"
    if path.exists():
        overwrite = _ask(f"{path.name} existe déjà. Écraser ? (o/N)", required=False, default="n")
        if overwrite.lower() not in ("o", "oui", "y", "yes"):
            print("Abandon.")
            sys.exit(0)

    emoji = _ask("Emoji (ex: 💜)")
    couleur = _ask("Couleur hex (ex: #a855f7)")
    role = _ask("Rôle / fonction (1 phrase)")
    print()
    personnalite = _ask("Personnalité (texte libre, multiligne)", multiline=True)
    print()
    traits = _ask_list("Traits de caractère")
    print()
    style_de_parole = _ask("Style de parole (texte libre, multiligne)", multiline=True)
    print()
    sujets_fetiches = _ask_list("Sujets fétiches")
    print()
    blagues_recurrentes = _ask_list("Blagues récurrentes")
    print()
    image_rel = _ask(
        "Chemin avatar dans /public (ex: /avatars/nova.webp) — laisse vide si pas d'image",
        required=False,
        default="",
    ).strip() or None

    data = {
        "prenom": prenom,
        "emoji": emoji,
        "couleur": couleur,
        "role": role,
        "personnalite": personnalite,
        "traits": traits,
        "style_de_parole": style_de_parole,
        "sujets_fetiches": sujets_fetiches,
        "blagues_recurrentes": blagues_recurrentes,
        "retours_humains": [],
    }

    PERSONNAGES_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n✓ Personnage écrit : {path}")

    if _update_characters_ts(prenom, couleur, emoji, image_rel):
        print(f"✓ Ajouté dans {CHARACTERS_TS.relative_to(CHARACTERS_TS.parent.parent)}")

    if image_rel:
        avatar_file = CHARACTERS_TS.parent.parent / "public" / image_rel.lstrip("/")
        if not avatar_file.exists():
            print(f"[!] Pense à déposer l'image à : {avatar_file}")

    print("\nC'est prêt. Le personnage sera utilisé au prochain run du pipeline.")


if __name__ == "__main__":
    creer_personnage()
