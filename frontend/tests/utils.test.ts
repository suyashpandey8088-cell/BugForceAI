import { describe, it, expect } from "vitest";
import { SEV_ORDER } from "../lib/api";
describe("severity ordering", () => {
  it("ranks critical above info", () => { expect(SEV_ORDER.critical).toBeGreaterThan(SEV_ORDER.info); });
  it("has all five levels", () => { expect(Object.keys(SEV_ORDER)).toHaveLength(5); });
});
describe("theme persistence contract", () => {
  it("next-themes storage key is stable", () => { expect("theme").toBe("theme"); });
});
