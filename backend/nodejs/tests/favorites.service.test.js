import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("../src/repositories/favorites.repository.js", () => ({
  destinationExists: vi.fn(),
  insertFavoriteIgnore: vi.fn(),
  deleteFavorite: vi.fn(),
  listFavoriteDestinationsByUserId: vi.fn()
}));

vi.mock("../src/shared/dto/destinationDto.js", () => ({
  attachDestinationImages: vi.fn(async (rows) => rows),
  toDestinationDto: vi.fn((row, isFavorite) => ({ ...row, isFavorite }))
}));

import * as favoritesRepository from "../src/repositories/favorites.repository.js";
import {
  addUserFavorite,
  removeUserFavorite
} from "../src/services/favorites.service.js";

describe("favorites.service", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("addUserFavorite returns not found when destination missing", async () => {
    favoritesRepository.destinationExists.mockResolvedValue(false);
    const result = await addUserFavorite(1, 404);
    expect(result).toEqual({ ok: false, reason: "destination_not_found" });
    expect(favoritesRepository.insertFavoriteIgnore).not.toHaveBeenCalled();
  });

  it("addUserFavorite inserts when destination exists", async () => {
    favoritesRepository.destinationExists.mockResolvedValue(true);
    favoritesRepository.insertFavoriteIgnore.mockResolvedValue(undefined);
    const result = await addUserFavorite(1, 7);
    expect(result).toEqual({ ok: true });
    expect(favoritesRepository.insertFavoriteIgnore).toHaveBeenCalledWith(1, 7);
  });

  it("removeUserFavorite deletes row", async () => {
    favoritesRepository.deleteFavorite.mockResolvedValue(undefined);
    const result = await removeUserFavorite(2, 9);
    expect(result).toEqual({ ok: true });
    expect(favoritesRepository.deleteFavorite).toHaveBeenCalledWith(2, 9);
  });
});
