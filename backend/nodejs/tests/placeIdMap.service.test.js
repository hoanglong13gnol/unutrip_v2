import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("../src/repositories/placeIdMap.repository.js", () => ({
  getDestinationIdByRagPlaceId: vi.fn()
}));

import * as placeIdMapRepository from "../src/repositories/placeIdMap.repository.js";
import {
  extractRawPlaceId,
  resolveRawPlaceIds
} from "../src/services/placeIdMap.service.js";

describe("placeIdMap.service", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("extractRawPlaceId prefers rawPlaceId", () => {
    expect(extractRawPlaceId({ rawPlaceId: " FIX_1 " })).toBe("FIX_1");
    expect(extractRawPlaceId({ place_id: "p2" })).toBe("p2");
    expect(extractRawPlaceId({})).toBeNull();
  });

  it("resolveRawPlaceIds batches unique ids", async () => {
    placeIdMapRepository.getDestinationIdByRagPlaceId.mockImplementation(async (id) => {
      if (id === "a") return 10;
      if (id === "b") return null;
      return null;
    });

    const { resolved, unresolved } = await resolveRawPlaceIds(["a", "b", "a"]);
    expect(resolved.get("a")).toBe(10);
    expect(unresolved).toEqual(["b"]);
    expect(placeIdMapRepository.getDestinationIdByRagPlaceId).toHaveBeenCalledTimes(2);
  });
});
