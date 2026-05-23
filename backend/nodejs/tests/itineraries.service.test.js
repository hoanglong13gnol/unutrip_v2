import { describe, it, expect, vi, beforeEach } from "vitest";

const withTransactionMock = vi.fn(async (fn) => fn({}));

vi.mock("../src/shared/db/withTransaction.js", () => ({
  withTransaction: (...args) => withTransactionMock(...args)
}));

vi.mock("../src/repositories/itineraries.repository.js", () => ({
  insertItinerary: vi.fn(),
  insertItineraryDay: vi.fn(),
  insertItineraryItem: vi.fn(),
  getItineraryById: vi.fn()
}));

import * as itinerariesRepository from "../src/repositories/itineraries.repository.js";
import { createItineraryWithDaysAndItems } from "../src/services/itineraries.service.js";

describe("itineraries.service createItineraryWithDaysAndItems", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    itinerariesRepository.insertItinerary.mockResolvedValue({ lastInsertRowid: 42 });
    itinerariesRepository.insertItineraryDay
      .mockResolvedValueOnce({ lastInsertRowid: 101 })
      .mockResolvedValueOnce({ lastInsertRowid: 102 });
    itinerariesRepository.insertItineraryItem.mockResolvedValue({ lastInsertRowid: 1 });
    itinerariesRepository.getItineraryById.mockResolvedValue({
      id: 42,
      user_id: 7,
      title: "Da Nang trip",
      description: "Test",
      start_date: "2026-06-01",
      end_date: "2026-06-02",
      total_days: 2,
      estimated_budget: 1000000,
      created_at: "2026-05-23T00:00:00.000Z",
      updated_at: "2026-05-23T00:00:00.000Z"
    });
  });

  it("creates itinerary days and distributes destination ids (max 2 per day)", async () => {
    const dto = await createItineraryWithDaysAndItems({
      userId: 7,
      payload: {
        title: "Da Nang trip",
        description: "Test",
        startDate: "2026-06-01",
        endDate: "2026-06-02",
        destinationIds: [1, 2, 3],
        estimatedBudget: 1000000,
        totalDays: 2
      }
    });

    expect(withTransactionMock).toHaveBeenCalledTimes(1);
    expect(itinerariesRepository.insertItinerary).toHaveBeenCalledWith(
      expect.objectContaining({
        userId: 7,
        title: "Da Nang trip",
        totalDays: 2,
        startDate: "2026-06-01",
        endDate: "2026-06-02"
      }),
      expect.anything()
    );
    expect(itinerariesRepository.insertItineraryDay).toHaveBeenCalledTimes(2);
    expect(itinerariesRepository.insertItineraryItem).toHaveBeenCalledTimes(3);
    expect(itinerariesRepository.getItineraryById).toHaveBeenCalledWith(42);
    expect(dto).toMatchObject({ id: 42, title: "Da Nang trip", totalDays: 2 });
  });
});
