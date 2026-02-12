<template>
  <div ref="mapEl" class="h-[330px] w-full rounded-xl border border-slate-200 shadow-sm"></div>
</template>

<script setup>
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";

const props = defineProps({
  lat: { type: Number, default: 46.603354 },
  lon: { type: Number, default: 1.888334 },
});

const emit = defineEmits(["moved"]);

const mapEl = ref(null);
let map = null;
let marker = null;

// Force explicit marker asset URLs for bundlers (Vite/nginx build).
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

onMounted(() => {
  if (!mapEl.value) return;
  map = L.map(mapEl.value).setView([props.lat || 46.603354, props.lon || 1.888334], props.lat && props.lon ? 15 : 5);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(map);

  marker = L.marker([props.lat || 46.603354, props.lon || 1.888334], { draggable: true }).addTo(map);
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
