#!/bin/sh
# Etape 2/2 de la preparation OSRM : transforme la carte en graphe routier
# (profil voiture, algorithme MLD), pret a etre servi par osrm-routed.
#
# Ne refait le calcul que si la carte est plus recente que le graphe.
set -eu

cd /data
GRAPH=map.osrm

if [ -f "$GRAPH.mldgr" ] && [ "$GRAPH.mldgr" -nt map.osm.pbf ]; then
    echo "[osrm-prepare] Graphe deja a jour."
    exit 0
fi

echo "[osrm-prepare] Construction du graphe routier..."
osrm-extract -p /opt/car.lua map.osm.pbf
osrm-partition "$GRAPH"
osrm-customize "$GRAPH"
echo "[osrm-prepare] Graphe pret."
