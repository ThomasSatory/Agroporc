"""
Recherche de GIFs via l'API Giphy.

Nécessite la variable d'environnement GIPHY_API_KEY.
"""
import os
import random
import urllib.request
import urllib.parse
import json


GIPHY_API_KEY = os.environ.get("GIPHY_API_KEY", "")
GIPHY_SEARCH_URL = "https://api.giphy.com/v1/gifs/search"

# Ensemble des GIFs déjà utilisés dans la semaine (partagé entre les appels
# au sein d'un même process). Permet d'éviter de réutiliser un même GIF
# plusieurs fois dans la même pipeline hebdomadaire.
_used_gif_ids: set[str] = set()
_used_gif_urls: set[str] = set()


def reset_used_gifs() -> None:
    """Réinitialise la mémoire des GIFs utilisés."""
    _used_gif_ids.clear()
    _used_gif_urls.clear()


def register_used_url(url: str) -> None:
    """Marque une URL de GIF comme déjà utilisée cette semaine."""
    if url:
        _used_gif_urls.add(url)


def _extract_url(item: dict) -> str | None:
    images = item.get("images", {})
    downsized = images.get("downsized", {})
    return downsized.get("url") or images.get("original", {}).get("url")


def search_gif(query: str, limit: int = 25, rating: str = "pg-13") -> str | None:
    """
    Recherche un GIF sur Giphy et retourne l'URL d'un résultat varié.

    Prend plusieurs résultats, écarte ceux déjà utilisés dans la semaine,
    puis choisit aléatoirement parmi les restants pour garantir la variété.
    """
    if not GIPHY_API_KEY:
        print("[gif_search] GIPHY_API_KEY non définie, GIF ignoré")
        return None

    # Forcer le style "meme" pour obtenir des GIFs plus drôles/expressifs.
    q = query.strip()
    if "meme" not in q.lower():
        q = f"{q} meme"

    params = urllib.parse.urlencode({
        "api_key": GIPHY_API_KEY,
        "q": q,
        "limit": limit,
        "rating": rating,
        "lang": "fr",
    })

    try:
        url = f"{GIPHY_SEARCH_URL}?{params}"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        results = data.get("data", [])
        if not results:
            return None

        # Filtrer les GIFs déjà vus cette semaine
        fresh = [
            r for r in results
            if r.get("id") not in _used_gif_ids
            and (_extract_url(r) or "") not in _used_gif_urls
        ]

        chosen = random.choice(fresh) if fresh else random.choice(results)
        gif_url = _extract_url(chosen)
        if not gif_url:
            return None

        gif_id = chosen.get("id")
        if gif_id:
            _used_gif_ids.add(gif_id)
        _used_gif_urls.add(gif_url)
        return gif_url

    except Exception as e:
        print(f"[gif_search] Erreur recherche GIF '{query}': {e}")
        return None


def resolve_gif_queries(commentaires: list[dict]) -> list[dict]:
    """
    Parcourt les commentaires et résout les champs 'gif_query' en 'image_url'.
    """
    for c in commentaires:
        gif_query = c.pop("gif_query", None)
        if gif_query:
            url = search_gif(gif_query)
            if url:
                c["image_url"] = url
    return commentaires
