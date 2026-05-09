import { cn } from "./utils";

describe("cn utility", () => {
  it("merges conditional classes", () => {
    const result = cn("px-2", false && "hidden", "text-sm", true && "font-bold");
    expect(result).toContain("px-2");
    expect(result).toContain("text-sm");
    expect(result).toContain("font-bold");
    expect(result).not.toContain("hidden");
  });

  it("resolves tailwind conflicts with latest class", () => {
    const result = cn("px-2", "px-4", "text-xs", "text-sm");
    expect(result).toBe("px-4 text-sm");
  });
});
