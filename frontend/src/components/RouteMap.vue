<template>
  <div ref="mapEl" class="w-full rounded-xl border border-slate-200 shadow-sm" :style="{ height, isolation: 'isolate' }"></div>
</template>

<script setup>
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";
import { COLORS } from "../lib/colors";

const props = defineProps({
  routeGeometry: { type: Array, default: () => [] },
  myRouteGeometry: { type: Array, default: () => [] },
  routes: { type: Array, default: () => [] },
  selectedRouteIndex: { type: Number, default: 0 },
  driverCoords: { type: Array, default: null },
  passengerCoords: { type: Array, default: null },
  // Ou le passager descend, quand ce n'est pas la destination du conducteur.
  dropoffCoords: { type: Array, default: null },
  destCoords: { type: Array, default: null },
  height: { type: String, default: "280px" },
  routeLabel: { type: String, default: "" },
  // Vrai quand le backend n'a pas pu joindre le service d'itineraire :
  // le trace est alors une ligne droite et les durees sont approximatives.
  estimated: { type: Boolean, default: false },
});

const emit = defineEmits(["select-route"]);

L.Icon.Default.mergeOptions({ iconRetinaUrl: markerIcon2x, iconUrl: markerIcon, shadowUrl: markerShadow });

const mapEl = ref(null);
let map = null;
const routePalette = ["#2563eb", "#7c3aed", "#0891b2", "#b45309", "#0f766e", "#be123c"];

function routePoints(route) {
  if (Array.isArray(route)) return route;
  return route?.route_geometry || route?.geometry || [];
}

// Deux points a moins de ~300 m l'un de l'autre (meme seuil que le backend,
// SAME_PLACE_KM) : un seul marqueur suffit.
function samePlace(a, b) {
  if (!a || !b) return false;
  return Math.abs(a[0] - b[0]) < 0.003 && Math.abs(a[1] - b[1]) < 0.004;
}

function pointIcon(color, label) {
  return L.divIcon({
    html: `<div class="shared-map-point" style="--marker-color:${color}"><span>${label}</span></div>`,
    className: "",
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  });
}

function rankIcon(rank, selected) {
  const tone = ({ 1: "gold", 2: "silver", 3: "bronze" })[rank] || "standard";
  return L.divIcon({
    html: `<button type="button" class="shared-map-rank shared-map-rank--${tone}${selected ? " is-selected" : ""}" aria-label="Sélectionner le trajet classé ${rank}">${rank}</button>`,
    className: "",
    iconSize: [34, 34],
    iconAnchor: [17, 17],
  });
}

function addSingleRoute(bounds) {
  if (!props.routeGeometry?.length) return;
  L.polyline(props.routeGeometry, { color: COLORS.routeLine, weight: 4, opacity: 0.85 }).addTo(map);
  bounds.push(...props.routeGeometry);
  if (props.routeLabel) {
    const midpoint = props.routeGeometry[Math.floor(props.routeGeometry.length / 2)];
    L.marker(midpoint, { icon: L.divIcon({ className: "", html: "", iconSize: [0, 0] }), interactive: false })
      .bindTooltip(props.routeLabel, { permanent: true, direction: "top", className: "route-badge", offset: [0, -2] })
      .addTo(map);
  }
}

function addSharedRoutes(bounds) {
  props.routes.forEach((route, index) => {
    const points = routePoints(route);
    if (!points.length) return;
    const selected = index === props.selectedRouteIndex;
    const line = L.polyline(points, {
      color: selected ? "#1463df" : routePalette[index % routePalette.length],
      weight: selected ? 7 : 5,
      opacity: selected ? 1 : 0.27,
      lineCap: "round",
      lineJoin: "round",
      interactive: true,
    }).addTo(map);

    line.on("click", () => emit("select-route", index));
    line.on("mouseover", () => !selected && line.setStyle({ opacity: 0.72, weight: 6 }));
    line.on("mouseout", () => !selected && line.setStyle({ opacity: 0.27, weight: 5 }));

    const midpoint = points[Math.floor(points.length / 2)];
    const rank = Number(route.rank || index + 1);
    L.marker(midpoint, { icon: rankIcon(rank, selected), zIndexOffset: selected ? 1000 : 100 })
      .on("click", () => emit("select-route", index))
      .addTo(map);

    if (selected) {
      line.bringToFront();
      line.bindTooltip(`Choix n° ${rank} · +${Number(route.extra_time_min || 0).toFixed(1)} min`, {
        permanent: true,
        direction: "top",
        className: "route-badge route-badge--selected",
        offset: [0, -8],
      });
    }
    bounds.push(...points);
  });
}

// Mention affichee dans un coin de la carte, sous forme de controle Leaflet
// pour ne pas toucher a la mise en page des pages qui utilisent la carte.
function addEstimateNotice() {
  const notice = L.control({ position: "bottomleft" });
  notice.onAdd = () => {
    const el = L.DomUtil.create("div", "route-estimate-note");
    el.textContent = "Itinéraire estimé : durées approximatives";
    el.title = "Le service de calcul d'itinéraire est indisponible : le tracé est une ligne droite.";
    return el;
  };
  notice.addTo(map);
}

function buildMap() {
  if (!mapEl.value) return;
  map = L.map(mapEl.value, { zoomControl: true }).setView([46.603354, 1.888334], 5);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(map);

  const bounds = [];
  if (props.myRouteGeometry?.length) {
    L.polyline(props.myRouteGeometry, {
      color: COLORS.myRoute,
      weight: 4,
      opacity: props.routes.length ? 0.32 : 0.85,
      dashArray: "8 7",
    }).addTo(map);
    bounds.push(...props.myRouteGeometry);
  }

  if (props.routes.length) addSharedRoutes(bounds);
  else addSingleRoute(bounds);

  const selectedRoute = props.routes[props.selectedRouteIndex] || null;
  const driverCoords = selectedRoute?.driver_coords || props.driverCoords;
  const passengerCoords = selectedRoute?.passenger_coords || props.passengerCoords;
  const destCoords = selectedRoute?.campus_coords || props.destCoords;
  const dropoffCoords = selectedRoute?.passenger_dropoff_coords || props.dropoffCoords;

  if (driverCoords && !props.routes.length) {
    L.marker(driverCoords, { icon: pointIcon(COLORS.driver, "D") }).bindTooltip("Conducteur").addTo(map);
    bounds.push(driverCoords);
  }
  if (passengerCoords) {
    L.marker(passengerCoords, { icon: pointIcon(COLORS.passenger, "P") }).bindTooltip("Passager").addTo(map);
    bounds.push(passengerCoords);
  }
  if (destCoords) {
    L.marker(destCoords, { icon: pointIcon(COLORS.destination, "A") }).bindTooltip("Destination").addTo(map);
    bounds.push(destCoords);
  }
  // Depose en chemin (autre ecole, domicile au retour) : seulement si elle
  // ne se confond pas avec la destination du conducteur.
  if (dropoffCoords && !samePlace(dropoffCoords, destCoords)) {
    L.marker(dropoffCoords, { icon: pointIcon(COLORS.passenger, "↓") }).bindTooltip("Dépose du passager").addTo(map);
    bounds.push(dropoffCoords);
  }

  // En mode multi-trajets, c'est le trajet selectionne qui decide.
  if (props.estimated || selectedRoute?.route_estimated) addEstimateNotice();

  if (bounds.length) map.fitBounds(bounds, { padding: [38, 38] });
  window.setTimeout(() => map?.invalidateSize(), 0);
}

function rebuildMap() {
  map?.remove();
  map = null;
  buildMap();
}

onMounted(buildMap);
watch(
  () => [props.routeGeometry, props.myRouteGeometry, props.routes, props.selectedRouteIndex, props.driverCoords, props.passengerCoords, props.dropoffCoords, props.destCoords, props.routeLabel, props.estimated],
  rebuildMap,
  { deep: true },
);
onBeforeUnmount(() => {
  map?.remove();
  map = null;
});
</script>
