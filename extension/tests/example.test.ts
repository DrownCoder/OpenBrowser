import { describe, test, expect } from "bun:test";

describe("Test Framework Setup", () => {
  test("bun test framework is working", () => {
    expect(true).toBe(true);
  });

  test("basic math operations", () => {
    expect(1 + 1).toBe(2);
  });
});
