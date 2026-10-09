"""Cálculo de distância candidato ↔ loja (haversine).

Puro Python, sem dependência de PostGIS. Suficiente para volumes de
piloto. Migrar para PostGIS/GeoDjango quando escala exigir.
"""
import math


EARTH_RADIUS_KM = 6371.0


def haversine_km(lat1, lng1, lat2, lng2):
    """Distância em km entre dois pontos (lat/lng em graus)."""
    if None in (lat1, lng1, lat2, lng2):
        return None
    lat1_r = math.radians(float(lat1))
    lat2_r = math.radians(float(lat2))
    dlat = math.radians(float(lat2) - float(lat1))
    dlng = math.radians(float(lng2) - float(lng1))
    a = (math.sin(dlat / 2) ** 2
         + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlng / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_KM * c


def distance_candidate_to_store(candidate, store):
    """Km entre candidato e loja. Retorna None se faltar coordenada."""
    return haversine_km(
        candidate.latitude, candidate.longitude,
        getattr(store, 'latitude', None), getattr(store, 'longitude', None),
    )
