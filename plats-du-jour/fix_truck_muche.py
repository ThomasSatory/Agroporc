"""
Script one-shot : retire les plats du Truck Muche de la semaine courante.
À utiliser quand le scraper a remonté un vieux menu par erreur.

Usage : python fix_truck_muche.py
"""
import json
from datetime import date, timedelta
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from publish import publish_pdj
from scrapers import bistrot_trefle
from agent import diet_agent

OUTPUT_FILE = Path(__file__).parent / "output" / "pdj.json"
DAY_NAMES = ["LUNDI", "MARDI", "MERCREDI", "JEUDI", "VENDREDI"]


def remove_truck(entry: dict) -> dict:
    """Retire Le Truck Muche des plats et recalcule la recommandation si besoin."""
    plats = [p for p in entry.get("plats", []) if p.get("restaurant") != "Le Truck Muche"]
    entry["plats"] = plats

    # Si la recommandation pointait vers le Truck, on la supprime (sera None)
    for key in ("recommandation", "recommandation_goulaf"):
        reco = entry.get(key)
        if reco and "Truck" in reco.get("restaurant", ""):
            entry[key] = None

    return entry


def fix_today():
    """Corrige le pdj.json du jour et le republish."""
    if not OUTPUT_FILE.exists():
        print("[fix] Pas de pdj.json trouvé")
        return

    data = json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))
    truck_count = sum(1 for p in data.get("plats", []) if p.get("restaurant") == "Le Truck Muche")

    if truck_count == 0:
        print("[fix] Pas de Truck Muche dans le pdj du jour, rien à corriger")
        return

    data = remove_truck(data)
    OUTPUT_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[fix] Truck Muche retiré du pdj du jour ({data['date']})")

    publish_pdj(data)


def fix_future_days():
    """Republish les jours futurs de la semaine sans le Truck Muche."""
    today = date.today()
    today_idx = today.weekday()
    if today_idx >= 4:
        print("[fix] Pas de jours futurs à corriger (vendredi ou week-end)")
        return

    # Charger les données Trèfle de la semaine (toujours valides)
    try:
        trefle_semaine = bistrot_trefle.scrape_semaine()
    except Exception as e:
        print(f"[fix] Erreur scrape_semaine Trèfle : {e}")
        trefle_semaine = None

    if not trefle_semaine:
        print("[fix] Pas de données Trèfle pour la semaine")

    # Construire et publier chaque jour futur SANS le Truck Muche
    future_days = {}
    for day_name in DAY_NAMES[today_idx + 1:]:
        plats_jour = []
        if trefle_semaine and day_name in trefle_semaine:
            t = trefle_semaine[day_name]
            plats_jour.append({
                "restaurant": "Le Bistrot Trèfle",
                "plat": t["plat"],
                "prix": t["prix"],
            })
        if plats_jour:
            future_days[day_name] = plats_jour

    # Évaluer les plats
    future_evaluations = {}
    if future_days:
        print(f"[fix] Réévaluation des plats de {len(future_days)} jours futurs (sans Truck Muche)...")
        try:
            future_evaluations = diet_agent.evaluate_semaine(future_days)
        except Exception as e:
            print(f"[fix] Erreur évaluation : {e}")

    # Publier
    for i, day_name in enumerate(DAY_NAMES[today_idx + 1:], start=1):
        future_date = today + timedelta(days=i)
        day_eval = future_evaluations.get(day_name, {})
        day_plats = day_eval.get("plats", future_days.get(day_name, []))

        day_plats.append({
            "restaurant": "La Pause Gourmande",
            "plat": "Coming soon",
            "prix": "",
            "coming_soon": True,
        })

        future_output = {
            "date": str(future_date),
            "plats": day_plats,
            "recommandation": day_eval.get("recommandation"),
            "recommandation_goulaf": day_eval.get("recommandation_goulaf"),
        }
        publish_pdj(future_output)
        print(f"[fix] Jour futur republié : {day_name} ({future_date}) — sans Truck Muche")


if __name__ == "__main__":
    print("[fix] Correction : retrait du Truck Muche de la semaine...")
    fix_today()
    fix_future_days()
    print("[fix] Terminé !")
