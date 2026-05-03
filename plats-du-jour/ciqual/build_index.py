"""
Construit ciqual_index.json à partir des XML Ciqual.

Usage :
    python -m ciqual.build_index

Lit `data/alim_*.xml` et `data/compo_*.xml`, écrit `ciqual_index.json` au même niveau.
À relancer uniquement quand l'ANSES publie une nouvelle version de la table.
"""
import json
import xml.etree.ElementTree as ET
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
OUT = Path(__file__).parent / "ciqual_index.json"

# Constituants à extraire (cf. const_*.xml)
CONST_KCAL = "328"     # Energie, Règlement UE 1169/2011 (kcal/100 g)
CONST_PROT = "25000"   # Protéines, N x facteur de Jones (g/100 g)
CONST_PROT_FALLBACK = "25003"  # Protéines, N x 6.25 (g/100 g)
CONST_GLUC = "31000"   # Glucides (g/100 g)
CONST_LIP = "40000"    # Lipides (g/100 g)


def _txt(node) -> str:
    if node is None or node.text is None:
        return ""
    return node.text.strip()


def _to_float(s: str) -> float | None:
    if not s or s in ("-", "traces"):
        return None
    s = s.replace(",", ".").replace("<", "").strip()
    try:
        return float(s)
    except ValueError:
        return None


def _find_xml(prefix: str) -> Path:
    matches = sorted(DATA_DIR.glob(f"{prefix}*.xml"))
    if not matches:
        raise FileNotFoundError(f"Aucun XML trouvé pour {prefix}* dans {DATA_DIR}")
    return matches[-1]


def build() -> None:
    alim_path = _find_xml("alim_2")  # évite alim_grp
    compo_path = _find_xml("compo_")

    # 1. alim_code -> nom_fr, groupe
    print(f"Parsing {alim_path.name}…")
    alims: dict[str, dict] = {}
    for elem in ET.iterparse(alim_path, events=("end",)):
        _, node = elem
        if node.tag != "ALIM":
            continue
        code = _txt(node.find("alim_code"))
        if not code:
            continue
        alims[code] = {
            "nom": _txt(node.find("alim_nom_fr")),
            "grp": _txt(node.find("alim_grp_code")),
        }
        node.clear()

    print(f"  {len(alims)} aliments")

    # 2. (alim_code, const_code) -> teneur
    print(f"Parsing {compo_path.name}… (gros fichier, patience)")
    targets = {CONST_KCAL, CONST_PROT, CONST_PROT_FALLBACK, CONST_GLUC, CONST_LIP}
    teneurs: dict[tuple[str, str], float | None] = {}
    for elem in ET.iterparse(compo_path, events=("end",)):
        _, node = elem
        if node.tag != "COMPO":
            continue
        cc = _txt(node.find("const_code"))
        if cc in targets:
            ac = _txt(node.find("alim_code"))
            teneurs[(ac, cc)] = _to_float(_txt(node.find("teneur")))
        node.clear()

    print(f"  {len(teneurs)} couples (alim, const)")

    # 3. Index final
    out = []
    for code, info in alims.items():
        prot = teneurs.get((code, CONST_PROT))
        if prot is None:
            prot = teneurs.get((code, CONST_PROT_FALLBACK))
        out.append({
            "code": code,
            "nom": info["nom"],
            "grp": info["grp"],
            "kcal": teneurs.get((code, CONST_KCAL)),
            "prot": prot,
            "gluc": teneurs.get((code, CONST_GLUC)),
            "lip": teneurs.get((code, CONST_LIP)),
        })

    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    size_kb = OUT.stat().st_size // 1024
    print(f"✓ {OUT.name} écrit ({len(out)} aliments, {size_kb} ko)")


if __name__ == "__main__":
    build()
