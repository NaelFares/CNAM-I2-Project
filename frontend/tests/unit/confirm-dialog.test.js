import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it } from "vitest";
import { nextTick } from "vue";

import ConfirmDialog from "../../src/components/ConfirmDialog.vue";
import { useConfirmStore } from "../../src/stores/confirm";

describe("ConfirmDialog", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    document.body.innerHTML = "";
  });

  function mountDialog() {
    return mount(ConfirmDialog, { attachTo: document.body });
  }

  it("affiche le message et resout true quand on confirme", async () => {
    const wrapper = mountDialog();
    const answer = useConfirmStore().ask({
      title: "Détour total important",
      message: "Ce passager rallongerait votre trajet.",
      confirmLabel: "Accepter quand même",
    });
    await nextTick();

    expect(document.body.textContent).toContain("Ce passager rallongerait votre trajet.");
    const buttons = [...document.body.querySelectorAll("button")];
    buttons.find((button) => button.textContent.includes("Accepter quand même")).click();

    await expect(answer).resolves.toBe(true);
    await nextTick();
    expect(document.body.textContent).not.toContain("Ce passager rallongerait");
    wrapper.unmount();
  });

  it("resout false quand on annule ou qu'on appuie sur Echap", async () => {
    const wrapper = mountDialog();
    const store = useConfirmStore();

    const cancelled = store.ask({ title: "T", message: "M" });
    await nextTick();
    [...document.body.querySelectorAll("button")].find((button) => button.textContent.includes("Annuler")).click();
    await expect(cancelled).resolves.toBe(false);

    const escaped = store.ask({ title: "T", message: "M" });
    await nextTick();
    window.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" }));
    await expect(escaped).resolves.toBe(false);
    wrapper.unmount();
  });
});
