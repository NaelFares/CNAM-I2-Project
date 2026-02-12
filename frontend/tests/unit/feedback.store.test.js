import { beforeEach, describe, expect, it } from "vitest";
import { createPinia, setActivePinia } from "pinia";

import { useFeedbackStore } from "../../src/stores/feedback";

describe("feedback store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("sets success and clears", () => {
    const store = useFeedbackStore();
    store.showSuccess("ok");
    expect(store.kind).toBe("success");
    expect(store.text).toBe("ok");
    store.clear();
    expect(store.text).toBe("");
  });
});
