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
  destCoords: { type: Array, default: null },
  height: { type: String, default: "280px" },
  routeLabel: { type: String, default: "" },
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
      line.bindTooltip(`${Number(route.score || 0)} % compatible · +${Number(route.extra_time_min || 0).toFixed(1)} min`, {
        permanent: true,
        direction: "top",
        className: "route-badge route-badge--selected",
        offset: [0, -8],
      });
    }
    bounds.push(...points);
  });
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
  () => [props.routeGeometry, props.myRouteGeometry, props.routes, props.selectedRouteIndex, props.driverCoords, props.passengerCoords, props.destCoords, props.routeLabel],
  rebuildMap,
  { deep: true },
);
onBeforeUnmount(() => {
  map?.remove();
  map = null;
});
</script>
