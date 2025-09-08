import { describe, it, expect } from "vitest";
import { allowedExtension, maxSizeOk } from "../lib/file";

describe("file", () => {
  it("checks allowed extensions", () => {
    expect(allowedExtension("a.mp3")).toBe(true);
    expect(allowedExtension("a.wav")).toBe(true);
    expect(allowedExtension("a.exe")).toBe(false);
  });
  it("checks max size", () => {
    expect(maxSizeOk(1)).toBe(true);
  });
});

