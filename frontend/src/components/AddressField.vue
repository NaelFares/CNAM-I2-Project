<template>
  <div class="relative">
    <label v-if="label" :for="inputId" class="mb-1.5 block text-sm font-medium text-slate-700">{{ label }}</label>
    <Input
      :id="inputId"
      v-model="target.address"
      :placeholder="placeholder"
      autocomplete="off"
      @input="onInput"
    >
      <template #icon><component :is="icon" class="h-4 w-4" /></template>
    </Input>

    <!-- Suggestions en surimpression, sous le champ : elles ne poussent pas la page. -->
    <ul
      v-if="auto.suggestions.value.length"
      class="absolute inset-x-0 top-full z-30 mt-1 max-h-64 overflow-y-auto rounded-xl border border-slate-200 bg-white p-1 shadow-[0_8px_24px_rgba(15,23,42,0.12)]"
      role="listbox"
    >
      <li v-for="item in auto.suggestions.value" :key="`${item.display_name}-${item.lat}`">
        <button
          type="button"
          class="flex w-full items-start gap-2 rounded-lg px-3 py-2 text-left text-sm transition hover:bg-slate-50"
          @click="onSelect(item)"
        >
          <MapPin class="mt-0.5 h-4 w-4 shrink-0 text-slate-400" aria-hidden="true" />
          <span class="min-w-0">
            <span class="block truncate font-medium text-slate-800">{{ item.display_name }}</span>
            <span class="block truncate text-xs text-slate-500">{{ item.place_label }}</span>
          </span>
        </button>
      </li>
    </ul>

    <!-- Une adresse tapee sans etre choisie dans la liste n'a pas de
         coordonnees fiables : on le dit plutot que d'envoyer un faux point. -->
    <p v-if="target.address && target.confirmed === false" class="mt-1 text-xs text-warning">
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
  label: { type: String, default: "" },
  placeholder: { type: String, default: "Saisissez une adresse…" },
  icon: { type: [Object, Function], default: () => MapPin },
});

const emit = defineEmits(["selected"]);

const inputId = `address-${Math.random().toString(36).slice(2, 9)}`;
const auto = useAddressAutocomplete(props.target);

function onInput() {
  // Toute frappe invalide l'adresse : ses coordonnees ne correspondent plus.
  props.target.confirmed = false;
  auto.onInput();
}

function onSelect(item) {
  auto.select(item);
  props.target.confirmed = true;
  emit("selected", item);
}
</script>
