import { daysBetweenInclusive, toIsoDate } from "../utils.js";
import * as itinerariesRepository from "../repositories/itineraries.repository.js";
import { withTransaction } from "../shared/db/withTransaction.js";
import {
  attachDestinationImages,
  toDestinationDto
} from "../shared/dto/destinationDto.js";
import { itineraryRowToDto } from "../shared/dto/itineraryDto.js";

export async function listItinerariesForUser(userId) {
  const rows = await itinerariesRepository.listItinerariesByUserId(userId);
  return rows.map((r) => itineraryRowToDto(r, null));
}

export async function getItineraryForUser({ userId, itineraryId }) {
  return itinerariesRepository.getItineraryByIdForUser({ itineraryId, userId });
}

export async function getItineraryDetailForUser({ userId, itineraryId }) {
  const it = await itinerariesRepository.getItineraryByIdForUser({ itineraryId, userId });
  if (!it) {
    return { ok: false };
  }

  const days = await itinerariesRepository.listItineraryDaysByItineraryId(itineraryId);
  const dayDtos = [];
  for (const d of days) {
    const items = await itinerariesRepository.listItineraryItemsWithDestinationByDayId(d.id);
    const attachRows = items.map((row) => ({ ...row, id: row.destination_id }));
    const attachedRows = await attachDestinationImages(attachRows);
    const itemsWithImages = items.map((row, idx) => ({
      ...row,
      images_from_table: attachedRows[idx]?.images_from_table
    }));
    dayDtos.push({
      id: d.id,
      itineraryId: d.itinerary_id,
      dayNumber: d.day_number,
      date: d.date,
      items: itemsWithImages.map((i) => ({
        id: i.id,
        dayId: i.day_id,
        destinationId: i.destination_id,
        destination: toDestinationDto(i, false),
        startTime: i.start_time,
        endTime: i.end_time,
        note: i.note,
        orderIndex: i.order_index
      }))
    });
  }

  return { ok: true, data: itineraryRowToDto(it, dayDtos) };
}

export async function createItineraryWithDaysAndItems({ userId, payload }) {
  const {
    title,
    description,
    startDate,
    endDate,
    destinationIds,
    estimatedBudget,
    totalDays
  } = payload;

  const itineraryId = await withTransaction(async (conn) => {
    const info = await itinerariesRepository.insertItinerary(
      {
        userId,
        title,
        description,
        startDate: toIsoDate(startDate),
        endDate: toIsoDate(endDate),
        totalDays,
        estimatedBudget
      },
      conn
    );

    const newItineraryId = Number(info.lastInsertRowid);
    const destIds = Array.isArray(destinationIds) ? destinationIds : [];

    for (let d = 0; d < totalDays; d++) {
      const date = new Date(toIsoDate(startDate));
      date.setDate(date.getDate() + d);
      const dayInfo = await itinerariesRepository.insertItineraryDay(
        {
          itineraryId: newItineraryId,
          dayNumber: d + 1,
          date: toIsoDate(date)
        },
        conn
      );
      const dayId = Number(dayInfo.lastInsertRowid);

      const chunk = destIds.slice(d * 2, d * 2 + 2);
      for (const [idx, destId] of chunk.entries()) {
        await itinerariesRepository.insertItineraryItem(
          {
            dayId,
            destinationId: destId,
            startTime: idx === 0 ? "09:00" : "14:00",
            endTime: idx === 0 ? "12:00" : "17:00",
            note: null,
            orderIndex: idx
          },
          conn
        );
      }
    }

    return newItineraryId;
  });

  const it = await itinerariesRepository.getItineraryById(itineraryId);
  return itineraryRowToDto(it, null);
}

export async function addItineraryItem({ userId, itineraryId, payload }) {
  const { destinationId, dayId, startTime, endTime, note } = payload;

  if (!destinationId) {
    return { ok: false, reason: "missing_destination_id" };
  }

  const it = await itinerariesRepository.getItineraryByIdForUser({
    itineraryId,
    userId
  });
  if (!it) {
    return { ok: false, reason: "not_authorized" };
  }

  let targetDayId = dayId;
  if (!targetDayId) {
    const firstDayId = await itinerariesRepository.getFirstItineraryDayId(itineraryId);
    if (!firstDayId) {
      return { ok: false, reason: "no_days" };
    }
    targetDayId = firstDayId;
  } else {
    const dayRow = await itinerariesRepository.getItineraryDayByIdForItinerary({
      dayId: targetDayId,
      itineraryId
    });
    if (!dayRow) {
      return { ok: false, reason: "invalid_day" };
    }
  }

  const maxIdx = await itinerariesRepository.getMaxOrderIndexByDayId(targetDayId);
  const nextIdx = (maxIdx ?? -1) + 1;

  await itinerariesRepository.insertItineraryItem({
    dayId: targetDayId,
    destinationId,
    orderIndex: nextIdx,
    startTime: startTime || "09:00",
    endTime: endTime || "10:00",
    note: note || ""
  });

  return { ok: true };
}

export async function updateItineraryItemForUser({ userId, itineraryId, itemId, payload }) {
  const it = await itinerariesRepository.getItineraryByIdForUser({ itineraryId, userId });
  if (!it) {
    return { ok: false, reason: "not_authorized" };
  }

  const row = await itinerariesRepository.getItineraryItemJoinDayById(itemId);
  if (!row || Number(row.itinerary_id) !== Number(itineraryId)) {
    return { ok: false, reason: "not_found" };
  }

  const nextDayId = payload.dayId !== undefined ? Number(payload.dayId) : Number(row.day_id);
  if (nextDayId !== Number(row.day_id)) {
    const dayRow = await itinerariesRepository.getItineraryDayByIdForItinerary({
      dayId: nextDayId,
      itineraryId
    });
    if (!dayRow) {
      return { ok: false, reason: "invalid_day" };
    }
  }

  const nextDestinationId =
    payload.destinationId !== undefined ? Number(payload.destinationId) : Number(row.destination_id);

  const nextStart = payload.startTime !== undefined ? payload.startTime : row.start_time;
  const nextEnd = payload.endTime !== undefined ? payload.endTime : row.end_time;
  const nextNote = payload.note !== undefined ? payload.note : row.note;
  const nextOrder =
    payload.orderIndex !== undefined ? Number(payload.orderIndex) : Number(row.order_index);

  if (!nextDestinationId) {
    return { ok: false, reason: "missing_destination_id" };
  }

  await itinerariesRepository.updateItineraryItemById({
    itemId,
    dayId: nextDayId,
    destinationId: nextDestinationId,
    startTime: nextStart,
    endTime: nextEnd,
    note: nextNote,
    orderIndex: nextOrder
  });

  return { ok: true };
}

function plusOneCalendarDay(isoDate) {
  const base = toIsoDate(isoDate);
  const d = new Date(base);
  d.setDate(d.getDate() + 1);
  return d.toISOString().slice(0, 10);
}

function dateOffsetFromStart(startIso, indexZeroBased) {
  const d = new Date(toIsoDate(startIso));
  d.setDate(d.getDate() + indexZeroBased);
  return d.toISOString().slice(0, 10);
}

export async function addItineraryDayForUser({ userId, itineraryId }) {
  const it = await itinerariesRepository.getItineraryByIdForUser({ itineraryId, userId });
  if (!it) {
    return { ok: false, reason: "not_authorized" };
  }

  await withTransaction(async (conn) => {
    const days = await itinerariesRepository.listItineraryDaysByItineraryIdConn(itineraryId, conn);
    const nextNum = days.length + 1;
    const newDate =
      days.length === 0
        ? toIsoDate(it.start_date)
        : plusOneCalendarDay(days[days.length - 1].date);

    await itinerariesRepository.insertItineraryDay(
      { itineraryId, dayNumber: nextNum, date: newDate },
      conn
    );
    await itinerariesRepository.updateItineraryEndAndTotalByUser(
      { itineraryId, userId, endDate: newDate, totalDays: nextNum },
      conn
    );
  });

  return { ok: true };
}

export async function deleteItineraryDayForUser({ userId, itineraryId, dayId }) {
  const it = await itinerariesRepository.getItineraryByIdForUser({ itineraryId, userId });
  if (!it) {
    return { ok: false, reason: "not_authorized" };
  }

  const dayRow = await itinerariesRepository.getItineraryDayByIdForItinerary({
    dayId,
    itineraryId
  });
  if (!dayRow) {
    return { ok: false, reason: "not_found" };
  }

  const daysBefore = await itinerariesRepository.listItineraryDaysByItineraryId(itineraryId);
  if (daysBefore.length <= 1) {
    return { ok: false, reason: "last_day" };
  }

  await withTransaction(async (conn) => {
    await itinerariesRepository.deleteItineraryDayByIdForItinerary({ dayId, itineraryId }, conn);
    const remaining = await itinerariesRepository.listItineraryDaysByItineraryIdConn(
      itineraryId,
      conn
    );
    const startIso = toIsoDate(it.start_date);
    for (let i = 0; i < remaining.length; i += 1) {
      const row = remaining[i];
      const newNum = i + 1;
      const newDate = dateOffsetFromStart(startIso, i);
      await itinerariesRepository.updateItineraryDayNumberAndDate(
        { dayId: row.id, dayNumber: newNum, date: newDate },
        conn
      );
    }
    const newTotal = remaining.length;
    const newEnd =
      newTotal === 0 ? startIso : dateOffsetFromStart(startIso, newTotal - 1);
    await itinerariesRepository.updateItineraryEndAndTotalByUser(
      { itineraryId, userId, endDate: newEnd, totalDays: newTotal },
      conn
    );
  });

  return { ok: true };
}

export async function deleteItineraryItemForUser({ userId, itineraryId, itemId }) {
  const it = await itinerariesRepository.getItineraryByIdForUser({ itineraryId, userId });
  if (!it) {
    return { ok: false, reason: "not_authorized" };
  }

  const row = await itinerariesRepository.getItineraryItemJoinDayById(itemId);
  if (!row || Number(row.itinerary_id) !== Number(itineraryId)) {
    return { ok: false, reason: "not_found" };
  }

  await itinerariesRepository.deleteItineraryItemById(itemId);
  return { ok: true };
}

export async function updateItineraryForUser({ userId, itineraryId, payload }) {
  const {
    title,
    description,
    startDate,
    endDate,
    totalDays,
    status,
    estimatedBudget
  } = payload;

  await itinerariesRepository.updateItineraryByIdForUser({
    itineraryId,
    userId,
    title,
    description,
    startDate,
    endDate,
    totalDays,
    status,
    estimatedBudget
  });

  const updated = await itinerariesRepository.getItineraryById(itineraryId);
  return itineraryRowToDto(updated, null);
}

export async function deleteItineraryForUser({ userId, itineraryId }) {
  await itinerariesRepository.deleteItineraryByIdForUser({ itineraryId, userId });
}

export async function saveAiItinerary({ userId, payload }) {
  const { title, description, startDate, endDate, budget, days } = payload;

  const safeStartDate = startDate || new Date().toISOString().split("T")[0];
  const safeEndDate = endDate || safeStartDate;

  const totalDays = daysBetweenInclusive(safeStartDate, safeEndDate);
  const isoStart = toIsoDate(safeStartDate);
  const isoEnd = toIsoDate(safeEndDate);

  await withTransaction(async (conn) => {
    const itinRes = await itinerariesRepository.insertItinerary(
      {
        userId,
        title: title || "Lá»‹ch trÃ¬nh AI",
        description: description || "ÄÃ£ lÆ°u tá»« gá»£i Ã½ AI.",
        startDate: isoStart,
        endDate: isoEnd,
        totalDays,
        estimatedBudget: budget || null
      },
      conn
    );
    const itineraryId = itinRes.lastInsertRowid;

    if (days && Array.isArray(days)) {
      for (const day of days) {
        const d = new Date(isoStart);
        d.setDate(d.getDate() + ((day.dayNumber || 1) - 1));
        const dayDateStr = d.toISOString().split("T")[0];

        const dayRes = await itinerariesRepository.insertItineraryDay(
          {
            itineraryId,
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
  });
}
