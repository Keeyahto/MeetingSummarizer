import { describe, it, expect } from "vitest";
import { toHMS, formatDue } from "../lib/time";

describe("time", () => {
  it("formats seconds to HH:MM:SS", () => {
    expect(toHMS(0)).toBe("00:00:00");
    expect(toHMS(65)).toBe("00:01:05");
    expect(toHMS(3661)).toBe("01:01:01");
  });
  it("formats due date", () => {
    const s = formatDue("2025-09-10");
    expect(s).toMatch(/2025|Sep|09|10/);
  });
});

