<template>
  <div ref="mapEl" class="h-[330px] w-full rounded-xl border border-slate-200 shadow-sm" style="isolation: isolate;"></div>
</template>

<script setup>
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";

const props = defineProps({
  lat: { type: Number, default: 43.6045 },
  lon: { type: Number, default: 1.444 },
});

const emit = defineEmits(["moved"]);

const mapEl = ref(null);
let map = null;
let marker = null;

// URLs explicites, sinon les marqueurs disparaissent après le build Vite.
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

onMounted(() => {
  if (!mapEl.value) return;
  map = L.map(mapEl.value).setView([props.lat || 43.6045, props.lon || 1.444], props.lat && props.lon ? 15 : 12);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(map);

  marker = L.marker([props.lat || 43.6045, props.lon || 1.444], { draggable: true }).addTo(map);
  marker.on("dragend", () => {
    const next = marker?.getLatLng();
    if (!next) return;
    emit("moved", next.lat, next.lng);
  });

  map.on("click", (event) => {
    marker?.setLatLng(event.latlng);
    emit("moved", event.latlng.lat, event.latlng.lng);
  });
});

watch(
  () => [props.lat, props.lon],
  ([lat, lon]) => {
    if (!map || !marker) return;
    marker.setLatLng([lat, lon]);
    map.setView([lat, lon], 15);
  }
);

onBeforeUnmount(() => {
  map?.remove();
  map = null;
  marker = null;
});
</script>
