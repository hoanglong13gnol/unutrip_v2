import { describe, it, expect } from "vitest";
import { toDestinationDto } from "../src/shared/dto/destinationDto.js";

/** Stable Android-facing keys — do not rename without app migration. */
const ANDROID_DESTINATION_KEYS = [
  "id",
  "name",
  "description",
  "address",
  "city",
  "province",
  "latitude",
  "longitude",
  "category",
  "images",
  "rating",
  "reviewCount",
  "openTime",
  "closeTime",
  "entryFee",
  "tags",
  "isFavorite"
];

describe("Android destination DTO contract", () => {
  it("toDestinationDto exposes the stable field set", () => {
    const dto = toDestinationDto(
      {
        id: 1,
        name: "Test",
        description: "d",
        address: "a",
        city: "c",
        province: "p",
        latitude: 1,
        longitude: 2,
        category: "beach",
        rating: 4.5,
        review_count: 3,
        open_time: "08:00",
        close_time: "17:00",
        entry_fee: 0,
        tags_json: "[]",
        images_from_table: ["/img.jpg"]
      },
      false
    );

    expect(Object.keys(dto).sort()).toEqual(ANDROID_DESTINATION_KEYS.sort());
    expect(dto.reviewCount).toBe(3);
    expect(dto.images).toEqual(["/img.jpg"]);
  });
});
