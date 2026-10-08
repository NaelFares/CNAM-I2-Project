<template>
  <div>
    <label class="mb-1.5 block text-sm font-semibold text-slate-700">{{ label }}</label>
    <Input
      v-model="target.address"
      :placeholder="placeholder"
      autocomplete="off"
      @input="onInput"
    >
      <template #icon><component :is="icon" class="h-4 w-4" /></template>
    </Input>

    <ul
      v-if="auto.suggestions.value.length"
      class="mt-2 max-h-48 overflow-y-auto rounded-xl border border-slate-200 bg-white p-2 shadow-sm"
    >
      <li v-for="item in auto.suggestions.value" :key="`${item.display_name}-${item.lat}`">
        <button
          type="button"
          class="w-full rounded-lg px-3 py-2 text-left text-sm transition hover:bg-primary-soft"
          @click="onSelect(item)"
        >
          <div class="font-semibold text-slate-800">{{ item.display_name }}</div>
          <div class="text-xs text-slate-500">{{ item.place_label }}</div>
        </button>
      </li>
    </ul>

    <!-- Une adresse tapee sans etre choisie dans la liste n'a pas de
         coordonnees fiables : on le dit plutot que d'envoyer un faux point. -->
    <p v-if="target.address && !target.confirmed" class="mt-1 text-xs text-amber-700">
      Choisissez l'adresse dans la liste pour la valider.
    </p>
  </div>
</template>

<script setup>
import { MapPin } from "lucide-vue-next";

import { useAddressAutocomplete } from "../composables/useAddressAutocomplete";
import { Input } from "./ui";

const props = defineProps({
  // Objet reactif { address, lat, lon, placeLabel, confirmed }, modifie en place.
  target: { type: Object, required: true },
  label: { type: String, required: true },
  placeholder: { type: String, default: "Saisissez une adresse…" },
  icon: { type: [Object, Function], default: () => MapPin },
});

const auto = useAddressAutocomplete(props.target);

function onInput() {
  // Toute frappe invalide l'adresse : ses coordonnees ne correspondent plus.
  props.target.confirmed = false;
  auto.onInput();
}

function onSelect(item) {
  auto.select(item);
  props.target.confirmed = true;
}
</script>
