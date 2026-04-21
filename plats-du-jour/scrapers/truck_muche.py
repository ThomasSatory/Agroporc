"""
Scraper pour Le Truck Muche via Facebook (sans login).
La page est accessible publiquement.
Facebook transcrit automatiquement le texte des images dans l'attribut alt.

Stratégie cache :
- Le lundi : scrape Facebook et sauvegarde le menu de la semaine dans le cache
- Mardi-vendredi : lit directement depuis le cache, pas de Playwright
"""
import json
import re
from datetime import date, timedelta
from pathlib import Path
from playwright.async_api import async_playwright

PAGE_URL = "https://www.facebook.com/letruckmuche/"
DAY_NAMES = ["LUNDI", "MARDI", "MERCREDI", "JEUDI", "VENDREDI", "SAMEDI", "DIMANCHE"]
MOIS_FR = {
    "JANVIER": 1, "FEVRIER": 2, "FÉVRIER": 2, "MARS": 3, "AVRIL": 4,
    "MAI": 5, "JUIN": 6, "JUILLET": 7, "AOUT": 8, "AOÛT": 8,
    "SEPTEMBRE": 9, "OCTOBRE": 10, "NOVEMBRE": 11, "DECEMBRE": 12, "DÉCEMBRE": 12,
}
CACHE_FILE = Path(__file__).parent.parent / "output" / "truck_muche_semaine.json"


# ── Cache ────────────────────────────────────────────────────────────────────

def _load_cache() -> dict | None:
    """Charge le cache si il correspond à la semaine en cours (lundi = date de référence)."""
    if not CACHE_FILE.exists():
        return None
    try:
        data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        # Le cache est valide si son lundi correspond au lundi de cette semaine
        today = date.today()
        lundi_semaine = today - timedelta(days=today.weekday())
        if data.get("lundi") == str(lundi_semaine):
            return data
    except Exception:
        pass
    return None


def _save_cache(menu_semaine: dict[str, str]) -> None:
    """Sauvegarde le menu de la semaine avec le lundi comme clé de validité."""
    today = date.today()
    lundi_semaine = today - timedelta(days=today.weekday())
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(
        json.dumps({"lundi": str(lundi_semaine), "menu": menu_semaine}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[truck_muche] Menu de la semaine mis en cache ({CACHE_FILE.name})")


# ── Scraping Facebook ────────────────────────────────────────────────────────

async def _scrape_facebook() -> str | None:
    """Lance Playwright et retourne le texte OCR de l'image du menu hebdomadaire."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--window-size=1280,900"],
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="fr-FR",
            viewport={"width": 1280, "height": 900},
        )
        page = await context.new_page()

        try:
            await page.goto(PAGE_URL, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)
        except Exception as e:
            print(f"[truck_muche] Erreur navigation : {e}")
            await browser.close()
            return None

        # Fermer les popups via JS (le bouton "Fermer" est un DIV, pas un <button>)
        await page.evaluate("""async () => {
            const delay = ms => new Promise(r => setTimeout(r, ms));
            for (const el of document.querySelectorAll('button, [role=button]')) {
                const t = el.innerText || '';
                if (t.includes('Autoriser') && t.includes('cookies')) {
                    el.click();
                    await delay(1000);
                    break;
                }
            }
            for (const el of document.querySelectorAll('[aria-label="Fermer"], [aria-label="Close"]')) {
                el.click();
                await delay(500);
            }
        }""")
        await page.wait_for_timeout(1500)

        # Scroller lentement pour déclencher le lazy-loading et l'OCR Facebook
        menu_text = await page.evaluate("""async () => {
            const delay = ms => new Promise(r => setTimeout(r, ms));
            for (let pos = 0; pos <= 6000; pos += 400) {
                window.scrollTo(0, pos);
                await delay(800);
                for (const img of document.querySelectorAll('img[alt]')) {
                    const alt = img.alt || '';
                    if (alt.toUpperCase().includes('PLATS DU JOUR') ||
                        (alt.toUpperCase().includes('LUNDI') && alt.toUpperCase().includes('MARDI'))) {
                        return alt;
                    }
                }
            }
            return null;
        }""")

        await browser.close()
        return menu_text


# ── Validation de la date ────────────────────────────────────────────────────

def _menu_est_semaine_courante(text: str) -> bool:
    """
    Vérifie que la date inscrite sur le menu correspond à la semaine en cours.
    Cherche un pattern type "DU 20 AU 24 AVRIL" dans le texte OCR.
    """
    text_upper = text.upper()
    # Pattern : "DU <jour_debut> AU <jour_fin> <mois>"
    match = re.search(r"DU\s+(\d{1,2})\s+AU\s+(\d{1,2})\s+([A-ZÀ-Ü]+)", text_upper)
    if not match:
        print("[truck_muche] Aucune date trouvée dans le menu, impossible de valider la semaine")
        return False

    jour_debut = int(match.group(1))
    mois_str = match.group(3)
    mois = MOIS_FR.get(mois_str)
    if not mois:
        print(f"[truck_muche] Mois non reconnu : {mois_str}")
        return False

    today = date.today()
    # Déduire l'année (si on est en janvier et le menu dit décembre, c'est l'année précédente)
    annee = today.year
    if today.month <= 2 and mois >= 11:
        annee -= 1
    elif today.month >= 11 and mois <= 2:
        annee += 1

    try:
        date_debut_menu = date(annee, mois, jour_debut)
    except ValueError:
        print(f"[truck_muche] Date invalide : {jour_debut}/{mois}/{annee}")
        return False

    lundi_semaine = today - timedelta(days=today.weekday())
    vendredi_semaine = lundi_semaine + timedelta(days=4)

    if lundi_semaine <= date_debut_menu <= vendredi_semaine:
        print(f"[truck_muche] Date du menu ({date_debut_menu}) correspond à la semaine en cours")
        return True
    else:
        print(f"[truck_muche] Date du menu ({date_debut_menu}) ne correspond PAS à la semaine en cours ({lundi_semaine} → {vendredi_semaine})")
        return False


# ── Parsing OCR ──────────────────────────────────────────────────────────────

def _parse_menu_semaine(text: str) -> dict[str, str]:
    """
    Parse le texte OCR complet et retourne un dict { "LUNDI": "plat", "MARDI": "plat", ... }
    """
    text_upper = text.upper()
    menu = {}

    for i, day in enumerate(DAY_NAMES[:5]):  # lundi → vendredi
        idx = text_upper.find(day)
        if idx == -1:
            continue

        after = text_upper[idx + len(day):]

        # Fin = prochain jour de la semaine
        next_idx = len(after)
        for other_day in DAY_NAMES:
            pos = after.find(other_day)
            if pos > 0:
                next_idx = min(next_idx, pos)

        plat_raw = after[:next_idx].strip()
        # Supprimer les caractères non-latin (parasites OCR) et la ponctuation excessive
        plat_raw = "".join(c for c in plat_raw if c.isascii() or c in "àâäéèêëîïôùûüçœæÀÂÄÉÈÊËÎÏÔÙÛÜÇŒÆ")
        plat_raw = " ".join(w for w in plat_raw.split() if not all(c in ".'`" for c in w))  # supprimer les tokens parasites (.....)
        plat = _deduplicate_ocr(plat_raw)
        if plat:
            menu[day] = plat

    return menu


def _deduplicate_ocr(text: str) -> str:
    """
    Facebook OCR duplique parfois les mots sous deux formes :
    - "PENNEBOLO PENNE BOLO"      → token collé AVANT les vrais mots
    - "POULET POULETBASQUAISE BASQUAISE" → token collé ENTRE les deux vrais mots
    """
    tokens = text.split()
    result = []
    i = 0
    while i < len(tokens):
        tok = tokens[i].upper()

        # Cas 1 : token collé entre prev et next ("POULET POULETBASQUAISE BASQUAISE")
        if (result and i + 1 < len(tokens) and len(tok) > 4 and
                tok == (result[-1] + tokens[i + 1]).upper()):
            i += 1
            continue

        # Cas 2 : token collé avant les vrais mots ("PENNEBOLO PENNE BOLO")
        skip = False
        for length in range(2, min(5, len(tokens) - i)):
            combined = "".join(tokens[i + 1: i + 1 + length]).upper()
            if tok == combined and len(tok) > 4:
                skip = True
                break

        if not skip:
            result.append(tokens[i])
        i += 1
    return " ".join(result).strip()


# ── Point d'entrée ───────────────────────────────────────────────────────────

async def scrape_semaine() -> dict[str, dict] | None:
    """
    Retourne un dict { "LUNDI": {"plat": str, "prix": str}, ... } pour toute la semaine.
    Scrape Facebook si pas de cache, sinon lit le cache.
    """
    cache = _load_cache()

    if cache is None:
        print("[truck_muche] Scraping Facebook pour le menu de la semaine...")
        menu_text = await _scrape_facebook()
        if not menu_text:
            print("[truck_muche] Aucun menu trouvé → Le Truck Muche est fermé cette semaine")
            return None  # fermé

        if not _menu_est_semaine_courante(menu_text):
            print("[truck_muche] Le menu sur Facebook n'est pas celui de cette semaine → Le Truck Muche est fermé cette semaine")
            return None

        menu_semaine = _parse_menu_semaine(menu_text)
        if not menu_semaine:
            print("[truck_muche] Impossible de parser le menu → Le Truck Muche est fermé cette semaine")
            return None  # fermé

        _save_cache(menu_semaine)
    else:
        print("[truck_muche] Menu chargé depuis le cache")
        menu_semaine = cache["menu"]

    semaine = {}
    for day, plat_raw in menu_semaine.items():
        options = [p.strip() for p in plat_raw.split(" OU ") if p.strip()]
        semaine[day] = {
            "plat": " ou ".join(options) if len(options) > 1 else options[0],
            "prix": "11.50€",
        }

    print(f"[truck_muche] {len(semaine)}/5 jours récupérés pour la semaine")
    return semaine


async def scrape() -> dict | None:
    """
    Retourne un dict { "restaurant": str, "plat": str, "prix": str } ou None si échec.
    Le lundi : scrape Facebook + met en cache le menu de la semaine.
    Mardi-vendredi : lit depuis le cache, pas de Playwright.
    """
    today = date.today()
    today_name = DAY_NAMES[today.weekday()]

    # Charger le cache
    cache = _load_cache()

    if cache is None and today.weekday() != 0:
        # Pas de cache et on n'est pas lundi → scraper quand même en fallback
        print("[truck_muche] Cache absent en dehors du lundi → scraping Facebook en fallback")

    if cache is None:
        # Scraper Facebook (lundi ou fallback)
        print("[truck_muche] Scraping Facebook pour le menu de la semaine...")
        menu_text = await _scrape_facebook()
        if not menu_text:
            print("[truck_muche] Aucun menu trouvé → Le Truck Muche est fermé cette semaine")
            return None  # fermé

        if not _menu_est_semaine_courante(menu_text):
            print("[truck_muche] Le menu sur Facebook n'est pas celui de cette semaine → Le Truck Muche est fermé cette semaine")
            return None

        menu_semaine = _parse_menu_semaine(menu_text)
        if not menu_semaine:
            print("[truck_muche] Impossible de parser le menu → Le Truck Muche est fermé cette semaine")
            return None  # fermé

        _save_cache(menu_semaine)
        cache = {"menu": menu_semaine}
    else:
        print("[truck_muche] Menu chargé depuis le cache (pas de scraping Facebook)")

    plat = cache["menu"].get(today_name)
    if not plat:
        print(f"[truck_muche] Pas de plat trouvé pour {today_name} dans le cache")
        return None

    # Séparer les options si plusieurs plats du jour ("POULET BASQUAISE OU FILET MIGNON")
    options = [p.strip() for p in plat.split(" OU ") if p.strip()]

    return {
        "restaurant": "Le Truck Muche",
        "plat": options if len(options) > 1 else options[0],
        "prix": "11.50€",
    }
