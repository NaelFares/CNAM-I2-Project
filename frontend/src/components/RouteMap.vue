<template>
  <div ref="mapEl" class="h-[280px] w-full rounded-xl border border-slate-200 shadow-sm"></div>
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
  routeGeometry: { type: Array, default: () => [] }, // [[lat, lon], ...]
  driverCoords: { type: Array, default: null },       // [lat, lon]
  passengerCoords: { type: Array, default: null },    // [lat, lon]
  destCoords: { type: Array, default: null },         // [lat, lon]
});

L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

const mapEl = ref(null);
let map = null;

function buildMap() {
  if (!mapEl.value) return;

  map = L.map(mapEl.value).setView([46.603354, 1.888334], 5);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(map);

  const bounds = [];

  if (props.routeGeometry?.length) {
    const polyline = L.polyline(props.routeGeometry, { color: COLORS.routeLine, weight: 4, opacity: 0.8 }).addTo(map);
    bounds.push(...props.routeGeometry);
  }

  const driverIcon = L.divIcon({
    html: `<div style="background:${COLORS.driver};width:14px;height:14px;border-radius:50%;border:2px solid white;box-shadow:0 1px 4px rgba(0,0,0,.4)"></div>`,
    className: "",
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  });

  const passengerIcon = L.divIcon({
    html: `<div style="background:${COLORS.passenger};width:14px;height:14px;border-radius:50%;border:2px solid white;box-shadow:0 1px 4px rgba(0,0,0,.4)"></div>`,
    className: "",
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  });

  const destIcon = L.divIcon({
    html: `<div style="background:${COLORS.destination};width:14px;height:14px;border-radius:50%;border:2px solid white;box-shadow:0 1px 4px rgba(0,0,0,.4)"></div>`,
    className: "",
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  });

  if (props.driverCoords) {
    L.marker(props.driverCoords, { icon: driverIcon }).bindTooltip("Conducteur").addTo(map);
    bounds.push(props.driverCoords);
  }

  if (props.passengerCoords) {
    L.marker(props.passengerCoords, { icon: passengerIcon }).bindTooltip("Passager").addTo(map);
    bounds.push(props.passengerCoords);
  }

  if (props.destCoords) {
    L.marker(props.destCoords, { icon: destIcon }).bindTooltip("Destination").addTo(map);
    bounds.push(props.destCoords);
  }

  if (bounds.length) {
    map.fitBounds(bounds, { padding: [20, 20] });
  }
}

onMounted(() => buildMap());

watch(
  () => [props.routeGeometry, props.driverCoords, props.passengerCoords, props.destCoords],
  () => {
    map?.remove();
    map = null;
    buildMap();
  },
  { deep: true }
);

onBeforeUnmount(() => {
  map?.remove();
  map = null;
});
</script>
