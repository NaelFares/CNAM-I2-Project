import { defineStore } from "pinia";

const DISPLAY_MODE_KEY = "studride-display-mode";

export const useDisplayStore = defineStore("display", {
  state: () => ({
    mobilePreview: localStorage.getItem(DISPLAY_MODE_KEY) === "mobile",
  }),
  actions: {
    toggleDisplayMode() {
      this.mobilePreview = !this.mobilePreview;
      localStorage.setItem(DISPLAY_MODE_KEY, this.mobilePreview ? "mobile" : "desktop");
    },
  },
});
