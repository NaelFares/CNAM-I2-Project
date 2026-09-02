import { ref } from "vue";

import { reverseAddress, searchAddress } from "../api/endpoints";
import { useFeedbackStore } from "../stores/feedback";

// `target` is a reactive object with { address, lat, lon, placeLabel } fields
// that this composable reads/writes directly.
export function useAddressAutocomplete(target) {
  const feedback = useFeedbackStore();
  const suggestions = ref([]);

  async function onInput() {
    if (target.address.trim().length < 3) {
      suggestions.value = [];
      return;
    }
    try {
      suggestions.value = await searchAddress(target.address.trim());
    } catch {
      suggestions.value = [];
    }
  }

  function select(item) {
    target.address = item.display_name;
    target.lat = item.lat;
    target.lon = item.lon;
    target.placeLabel = item.place_label;
    suggestions.value = [];
  }

  async function locate() {
    if (!target.address.trim()) {
      feedback.showInfo("Saisissez d'abord une adresse.");
      return;
    }
    try {
      const results = await searchAddress(target.address.trim());
      if (!results.length) {
        feedback.showError("Adresse introuvable.");
        return;
      }
      select(results[0]);
      feedback.showSuccess("Adresse localisée sur la carte.");
    } catch {
      feedback.showError("La recherche d'adresse a échoué.");
    }
  }

  async function onMapMoved(lat, lon) {
    target.lat = lat;
    target.lon = lon;
    const result = await reverseAddress(lat, lon).catch(() => null);
    if (!result) return;
    target.address = result.display_name;
    target.placeLabel = result.place_label;
  }

  return { suggestions, onInput, select, locate, onMapMoved };
}
