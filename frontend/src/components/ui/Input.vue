<template>
  <div class="relative">
    <span
      v-if="$slots.icon"
      class="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400"
    >
      <slot name="icon" />
    </span>
    <input
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :class="['input', $slots.icon ? 'input-with-icon' : '']"
      v-bind="$attrs"
      @input="$emit('update:modelValue', $event.target.value)"
    />
  </div>
</template>

<script setup>
defineProps({
  modelValue: { type: [String, Number], default: "" },
  type: { type: String, default: "text" },
  placeholder: { type: String, default: "" },
  disabled: { type: Boolean, default: false },
});

defineEmits(["update:modelValue"]);
defineOptions({ inheritAttrs: false });
</script>
