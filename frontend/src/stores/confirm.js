import { defineStore } from "pinia";

// Demande de confirmation a l'utilisateur, affichee par ConfirmDialog.
// `ask` renvoie une promesse resolue a true (confirme) ou false (annule),
// pour s'utiliser comme window.confirm, mais avec le style de l'application.
export const useConfirmStore = defineStore("confirm", {
  state: () => ({
    open: false,
    title: "",
    message: "",
    confirmLabel: "Confirmer",
    cancelLabel: "Annuler",
    resolver: null,
  }),
  actions: {
    ask({ title, message, confirmLabel = "Confirmer", cancelLabel = "Annuler" }) {
      // Une demande deja ouverte est annulee : une seule a la fois.
      this.resolver?.(false);
      Object.assign(this, { open: true, title, message, confirmLabel, cancelLabel });
      return new Promise((resolve) => {
        this.resolver = resolve;
      });
    },
    answer(confirmed) {
      this.resolver?.(confirmed);
      this.resolver = null;
      this.open = false;
    },
  },
});
