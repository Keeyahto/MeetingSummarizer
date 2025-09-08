import { describe, it, expect } from "vitest";
import { useUiStore } from "../lib/store";

describe("store", () => {
  it("streams tokens", () => {
    const s = useUiStore.getState();
    s.startStream();
    s.appendToken("Hello ");
    s.appendToken("world");
    expect(useUiStore.getState().tldrStream).toBe("Hello world");
    s.stopStream();
    expect(useUiStore.getState().streaming).toBe(false);
  });
});

