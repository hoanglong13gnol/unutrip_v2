import { toIsoDate } from "../utils.js";
import * as itinerariesRepository from "../repositories/itineraries.repository.js";
import { withTransaction } from "../shared/db/withTransaction.js";

export async function persistAiSuggestedItinerary({
  userId,
  aiResult,
  isoStart,
  isoEnd,
  totalDays,
  budget
}) {
  const itineraryId = await withTransaction(async (conn) => {
    const itinRes = await itinerariesRepository.insertItinerary(
      {
        userId,
        title: aiResult.title || "Lá»‹ch trÃ¬nh AI táº¡o",
        description: aiResult.description || "Táº¡o bá»Ÿi HÆ°á»›ng dáº«n viÃªn du lá»‹ch áº£o.",
        startDate: isoStart,
        endDate: isoEnd,
        totalDays,
        estimatedBudget: budget || null
      },
      conn
    );
    const newItineraryId = itinRes.lastInsertRowid;

    if (aiResult.days && Array.isArray(aiResult.days)) {
      for (const day of aiResult.days) {
        const dayDate = new Date(isoStart);
        dayDate.setDate(dayDate.getDate() + ((day.dayNumber || 1) - 1));
        const dayDateStr = toIsoDate(dayDate.toISOString().split("T")[0]);

        const dayRes = await itinerariesRepository.insertItineraryDay(
          {
            itineraryId: newItineraryId,
            dayNumber: day.dayNumber || 1,
            date: dayDateStr
          },
          conn
        );
        const dayId = dayRes.lastInsertRowid;

        let orderIdx = 0;
        if (day.items && Array.isArray(day.items)) {
          for (const item of day.items) {
            await itinerariesRepository.insertItineraryItem(
              {
                dayId,
                destinationId: item.destinationId,
                orderIndex: orderIdx++,
                startTime: item.startTime || "08:00",
                endTime: item.endTime || "09:00",
                note: item.note || ""
              },
              conn
            );
          }
        }
      }
    }

    return newItineraryId;
  });

  return {
    id: itineraryId,
    userId,
    title: aiResult.title,
    description: aiResult.description,
    startDate: isoStart,
    endDate: isoEnd,
    totalDays,
    status: "planned",
    estimatedBudget: budget || null
  };
}
