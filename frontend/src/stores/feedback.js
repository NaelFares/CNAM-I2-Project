import { defineStore } from "pinia";

export const useFeedbackStore = defineStore("feedback", {
  state: () => ({
    kind: "",
    text: "",
    token: 0,
  }),
  actions: {
    showSuccess(text) {
      this.kind = "success";
      this.text = text;
      this.token += 1;
    },
    showInfo(text) {
      this.kind = "info";
      this.text = text;
      this.token += 1;
    },
    showError(text) {
      this.kind = "error";
      this.text = text;
      this.token += 1;
    },
    clear() {
      this.kind = "";
      this.text = "";
    },
  },
});
