#!/bin/sh
# Etape 1/2 de la preparation OSRM : telecharge la carte OpenStreetMap et la
# decoupe a la zone de l'application (OSRM_BBOX).
#
# Tourne une seule fois : si la carte decoupee existe deja pour la meme zone,
# le script s'arrete aussitot. Changer OSRM_BBOX relance la preparation.
set -eu

DATA_DIR=/data
MAP="$DATA_DIR/map.osm.pbf"
BBOX_STAMP="$DATA_DIR/map.bbox"
SOURCE="$DATA_DIR/source.osm.pbf"

if [ -f "$MAP" ] && [ "$(cat "$BBOX_STAMP" 2>/dev/null)" = "$OSRM_BBOX" ]; then
    echo "[osrm-map] Carte deja prete pour la zone $OSRM_BBOX."
    exit 0
fi

apt-get update -qq >/dev/null
apt-get install -y -qq --no-install-recommends ca-certificates curl osmium-tool >/dev/null

# Source principale : extrait "Toulouse" de BBBike (~65 Mo, mis a jour chaque
# semaine). Secours : region Geofabrik, plus lourde (~360 Mo) mais tres stable.
echo "[osrm-map] Telechargement de la carte..."
if ! curl -fL --retry 3 -o "$SOURCE" "$OSM_SOURCE_URL"; then
    echo "[osrm-map] Source principale indisponible, essai de $OSM_FALLBACK_URL"
    curl -fL --retry 3 -o "$SOURCE" "$OSM_FALLBACK_URL"
fi

# Decoupe a la zone utile. complete_ways garde entieres les routes qui
# traversent le bord de la zone, pour ne pas couper d'itineraire.
echo "[osrm-map] Decoupe a la zone $OSRM_BBOX..."
osmium extract --bbox "$OSRM_BBOX" --strategy complete_ways \
    --overwrite --output "$MAP" "$SOURCE"

rm -f "$SOURCE"
echo "$OSRM_BBOX" > "$BBOX_STAMP"
echo "[osrm-map] Carte prete : $(du -h "$MAP" | cut -f1)."
